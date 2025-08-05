# /main.py
import argparse
import json
import os
import subprocess
import threading
import configparser
import shutil

# --- CÁC HÀM PHỤ TRỢ ---

def run_module(command_args):
    """Thực thi một module worker và trả về kết quả JSON."""
    try:
        process = subprocess.run(command_args, capture_output=True, text=True, check=True, encoding='utf-8')
        if not process.stdout.strip(): return {}
        return json.loads(process.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi chạy module: {' '.join(command_args)}")
        print(f"Lỗi: {e.stderr or e.stdout}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Lỗi không mong muốn: {e}")
        return {"status": "error", "message": str(e)}

def get_files_from_dir(folder_path):
    """Lấy danh sách tất cả các file trong một thư mục."""
    all_files = []
    if not os.path.isdir(folder_path):
        return []
    for root, _, files in os.walk(folder_path):
        for file in files:
            all_files.append(os.path.join(root, file))
    return list(all_files)

def step_move_torrent(file_path, config_data):
    """Di chuyển file .torrent đã xử lý sang thư mục 'Downloaded'."""
    torrent_downloaded_dir = config_data.get('torrent_downloaded_dir')
    if not torrent_downloaded_dir:
        print("Lỗi: Không tìm thấy đường dẫn 'torrent_downloaded_dir' trong cấu hình.")
        return

    if not os.path.exists(torrent_downloaded_dir):
        os.makedirs(torrent_downloaded_dir, exist_ok=True)

    try:
        shutil.move(file_path, os.path.join(torrent_downloaded_dir, os.path.basename(file_path)))
        print(f" -> Đã di chuyển file .torrent: {os.path.basename(file_path)} -> {torrent_downloaded_dir}")
    except Exception as e:
        print(f" -> Lỗi khi di chuyển file .torrent {os.path.basename(file_path)}: {e}")

# --- CÁC BƯỚC XỬ LÝ CHÍNH ---

def step_filter_files(file_list, min_size_mb):
    """Lọc danh sách file theo dung lượng tối thiểu."""
    if min_size_mb <= 0:
        return file_list
    
    min_size_bytes = min_size_mb * 1024 * 1024
    print(f"\n[BƯỚC LỌC] Lọc các file nhỏ hơn {min_size_mb}MB...")
    
    filtered_list = []
    for f in file_list:
        try:
            if os.path.getsize(f) > min_size_bytes:
                filtered_list.append(f)
            else:
                print(f" -> Loại bỏ file rác: {os.path.basename(f)}")
        except FileNotFoundError:
            continue
            
    return filtered_list

def step_join_files(file_list, output_name):
    """Nối các file trong danh sách thành một file duy nhất."""
    if len(file_list) < 2:
        return file_list

    print(f"\n[BƯỚC NỐI FILE] Nối {len(file_list)} file...")
    
    first_file = file_list[0]
    output_dir = os.path.dirname(first_file)
    _, ext = os.path.splitext(first_file)
    final_output_name = (output_name if output_name else "joined_file") + ext
    output_path = os.path.join(output_dir, final_output_name)
    
    cmd = [
        'python3', 'core/joiner.py',
        '--files-json', json.dumps(sorted(file_list)),
        '--output-file', output_path,
        '--delete-parts'
    ]
    result = run_module(cmd)
    
    if result and result.get('status') == 'success':
        return [result.get('output_path')]
    else:
        print(" -> Nối file thất bại. Hủy bỏ quy trình.")
        return []

def step_split_files(file_list, max_gb, start_times):
    """Chia nhỏ các file, ưu tiên chế độ thủ công nếu có start_times."""
    final_files = []
    
    if start_times:
        print(f"\n[BƯỚC CHIA FILE] Chế độ thủ công theo các mốc thời gian: {start_times}")
        if len(file_list) > 1:
            print(" -> Cảnh báo: Chế độ chia thủ công chỉ áp dụng cho file đầu tiên trong danh sách.")
        
        f = file_list[0]
        cmd = [
            'python3', 'core/ffmpeg_splitter.py',
            '--file-path', f,
            '--start-times'
        ] + [str(t) for t in start_times]
        
        result = run_module(cmd)
        if result and result.get('status') == 'manual_split':
            final_files.extend(result.get('files', []))
        else:
            print(f" -> Chia file thủ công thất bại cho: {os.path.basename(f)}.")
        
        final_files.extend(file_list[1:])

    elif max_gb:
        print(f"\n[BƯỚC CHIA FILE] Chế độ tự động, kiểm tra các file lớn hơn {max_gb}GB...")
        for f in file_list:
            cmd = [
                'python3', 'core/ffmpeg_splitter.py',
                '--file-path', f,
                '--max-size-gb', str(max_gb)
            ]
            result = run_module(cmd)
            if result and result.get('status') in ['auto_split', 'unsplit']:
                final_files.extend(result.get('files', []))
            else:
                print(f" -> Chia file tự động thất bại cho: {os.path.basename(f)}. Bỏ qua file này.")
    else:
        return file_list
            
    return final_files

def step_upload_files(file_list, uploaders, creds, excel_config):
    """Tải các file trong danh sách lên các host chỉ định."""
    print(f"\n[BƯỚC UPLOAD] Bắt đầu upload lên: {', '.join(uploaders)}...")
    threads = []
    for f in file_list:
        for host in uploaders:
            thread = threading.Thread(target=uploader_task, args=(host, f, creds, excel_config))
            threads.append(thread)
            thread.start()
    for t in threads:
        t.join()

def step_store_files(file_list, save_dir):
    """Di chuyển các file cuối cùng vào thư mục lưu trữ."""
    print(f"\n[BƯỚC LƯU TRỮ] Di chuyển file đến: {save_dir}")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    for f in file_list:
        if os.path.exists(f):
            try:
                shutil.move(f, os.path.join(save_dir, os.path.basename(f)))
            except Exception as e:
                print(f" -> Lỗi khi di chuyển file {os.path.basename(f)}: {e}")

def uploader_task(host_name, file_path, creds, excel_config):
    """Tác vụ upload (dùng cho threading)."""
    print(f" -> Bắt đầu upload {os.path.basename(file_path)} lên {host_name}...")
    host_creds = creds.get(host_name)
    if not host_creds: return

    command = []
    if host_name == 'nitroflare':
        command = ['python3', 'uploaders/nitroflare_uploader.py', '-f', file_path, '-uh', host_creds.get('user_hash')]
    elif host_name == 'keep2share':
        command = ['python3', 'uploaders/keep2share_uploader.py', '-f', file_path, '-t', host_creds.get('access_token')]
    
    if not command: return
    upload_result = run_module(command)

    if excel_config and upload_result and upload_result.get('status') == 'success':
        link_data = json.dumps({
            "Name": os.path.basename(file_path),
            "Link": upload_result.get('upload_url'),
            "Host": f"{host_name}.com"
        })
        run_module(['python3', 'core/excel_handler.py', '-f', excel_config.get('excel_file'), '-s', 'Host_Storage', '-t', 'Host_Storage', '-a', 'write', '--data-json', link_data])

def process_files_pipeline(initial_files, args, config_data):
    """Hàm chung để chạy chuỗi xử lý file."""
    if not initial_files:
        print("Không tìm thấy file nào để xử lý.")
        return

    print(f"Tìm thấy {len(initial_files)} file nguồn để bắt đầu quy trình.")
    
    processed_files = step_filter_files(initial_files, args.min_size_mb)
    if not processed_files: print("Không có file nào đạt tiêu chuẩn sau khi lọc."); return

    if args.join_files:
        processed_files = step_join_files(processed_files, args.output_name)
    if not processed_files: print("Quy trình dừng sau bước Nối file."); return
        
    if args.split_max_gb or args.split_at_times:
        processed_files = step_split_files(processed_files, args.split_max_gb, args.split_at_times)
    if not processed_files: print("Quy trình dừng sau bước Chia file."); return

    if args.uploaders:
        upload_list = []
        if 'all' in args.uploaders:
            cfg = configparser.ConfigParser()
            cfg.read('account.txt')
            upload_list = cfg.sections()
        else:
            upload_list = args.uploaders
            
        creds = {}
        for host in upload_list:
            creds[host] = run_module(['python3', 'core/account.py', '-f', 'account.txt', '-s', host])
            
        excel_config = config_data if 'excel_file' in config_data else None
        step_upload_files(processed_files, upload_list, creds, excel_config)
        
    step_store_files(processed_files, config_data['save_dir'])
    
    print("\nQuy trình đã hoàn tất!")

# --- HÀM MAIN ---

def main():
    parser = argparse.ArgumentParser(description="Công cụ tự động hóa tải, xử lý và upload file.", add_help=False)
    
    required_args = parser.add_argument_group('Tham số bắt buộc')
    optional_args = parser.add_argument_group('Tham số tùy chọn')
    
    required_args.add_argument("-c", "--category", required=True, help="Chỉ định danh mục để lấy cấu hình (ví dụ: MyMovies).")
    
    # === DÒNG ĐÃ SỬA LỖI HIỂN THỊ ===
    WORKFLOW_CHOICES = ['url-download', 'torrent-download', 'magnet-download', 'process-local']
    optional_args.add_argument("-w", "--workflow", choices=WORKFLOW_CHOICES, help=f"Quy trình cần chạy. Lựa chọn: {', '.join(WORKFLOW_CHOICES)}.")
    
    optional_args.add_argument("--source-dir", help="Thư mục nguồn cho workflow 'process-local'.")
    optional_args.add_argument("--join-files", action='store_true', help="Bật tính năng Nối các file nguồn thành một.")
    optional_args.add_argument("--split-max-gb", type=int, help="Bật tính năng Chia file tự động và đặt dung lượng tối đa (GB).")
    optional_args.add_argument("--split-at-times", nargs='+', type=float, help="Bật tính năng Chia file thủ công theo các mốc thời gian (giây).")
    optional_args.add_argument("-up", "--uploaders", nargs='+', help="Bật tính năng Upload. Cung cấp tên host hoặc 'all'.")
    optional_args.add_argument("--min-size-mb", type=int, default=100, help="Ngưỡng dung lượng tối thiểu (MB). Mặc định: 100.")
    optional_args.add_argument("--output-name", help="Đặt tên cho file output (quan trọng khi dùng --join-files).")
    optional_args.add_argument("-h", "--help", action="help", help="Hiển thị thông báo trợ giúp và thoát.")

    args = parser.parse_args()
    
    config_data = run_module(['python3', 'core/config_handler.py', '-c', args.category])
    if not config_data or config_data.get('status') == 'error':
        print("Lỗi: Không thể lấy cấu hình cho category.")
        return
        
    if not args.workflow:
        print("Vui lòng chọn một workflow bằng tham số -w.")
        parser.print_help() # In ra toàn bộ hướng dẫn
        return
        
    initial_files = []
    
    if args.workflow == 'process-local':
        if not args.source_dir or not os.path.isdir(args.source_dir):
            print("Lỗi: Workflow 'process-local' yêu cầu tham số --source-dir hợp lệ.")
            return
        initial_files = get_files_from_dir(args.source_dir)
        process_files_pipeline(initial_files, args, config_data)

    elif args.workflow in ['url-download', 'torrent-download', 'magnet-download']:
        excel_file = config_data.get('excel_file')
        if not excel_file:
            print(f"Lỗi: Category '{args.category}' thiếu cấu hình 'excel_file' trong config_handler.py.")
            return
            
        sheet_map = {'url-download': 'DownLoadUrl', 'magnet-download': 'DownLoadMagnetLink', 'torrent-download': 'DownLoadTorrent'}
        sheet_name = sheet_map[args.workflow]
        
        tasks = run_module(['python3', 'core/excel_handler.py', '-f', excel_file, '-s', sheet_name, '-t', sheet_name, '-a', 'read'])
        if not tasks:
            print(f"Không có tác vụ nào trong sheet '{sheet_name}'.")
            return
            
        pending_tasks = [t for t in tasks if str(t.get('Downloaded', '')).lower() != 'downloaded']
        print(f"Tìm thấy {len(pending_tasks)} tác vụ cần xử lý từ Excel.")
        
        for i, task in enumerate(pending_tasks):
            print(f"\n--- Bắt đầu xử lý tác vụ {i+1}/{len(pending_tasks)}: {task.get('Name')} ---")
            
            download_dir = config_data['download_dir']
            files_before = set(get_files_from_dir(download_dir))
            
            downloader_script = f"downloaders/{args.workflow.split('-')[0]}_downloader.py"
            cmd_download = ['python3', downloader_script, '-o', download_dir]
            
            link = None
            task_name = task.get('Name')
            if not task_name:
                print(" -> Tác vụ thiếu 'Name'. Bỏ qua.")
                continue

            if args.workflow == 'url-download':
                link = task.get('Url')
                cmd_download.extend(['-u', link, '-n', task_name])
            elif args.workflow == 'magnet-download':
                link = task.get('MagnetLink')
                cmd_download.extend(['-m', link])
            elif args.workflow == 'torrent-download':
                link = task.get('TorrentPath', os.path.join(config_data.get('torrent_dir', ''), task_name))
                cmd_download.extend(['-t', link])

            if not link:
                print(" -> Tác vụ thiếu link. Bỏ qua.")
                continue

            download_result = run_module(cmd_download)
            if not download_result or download_result.get('status') != 'success':
                print(" -> Tải về thất bại. Dừng xử lý tác vụ này.")
                continue

            # BƯỚC XỬ LÝ MỚI: Di chuyển file .torrent
            if args.workflow == 'torrent-download' and 'torrent_downloaded_dir' in config_data:
                torrent_path_to_move = os.path.join(config_data.get('torrent_dir'), task_name)
                step_move_torrent(torrent_path_to_move, config_data)

            files_after = set(get_files_from_dir(download_dir))
            new_files = list(files_after - files_before)
            
            # Gán output_name từ excel cho bước join
            args.output_name = task_name
            process_files_pipeline(new_files, args, config_data)
            
            # Cập nhật trạng thái trong Excel
            run_module(['python3', 'core/excel_handler.py', '-f', excel_file, '-s', sheet_name, '-t', sheet_name, '-a', 'update', '--row-index', str(tasks.index(task)), '--column', 'Downloaded', '--value', 'downloaded'])
            print(f"--- Hoàn thành tác vụ: {task.get('Name')} ---")

if __name__ == '__main__':
    main()
