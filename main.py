# /main.py
import argparse
import json
import os
import subprocess
import threading
import shutil
from core import config_manager, excel_handler, file_utils

# --- CÁC HÀM TIỆN ÍCH ---

def run_module(command_args):
    """Thực thi một module worker và trả về kết quả JSON một cách an toàn."""
    try:
        process = subprocess.run(
            command_args, capture_output=True, text=True, check=True, encoding='utf-8'
        )
        if not process.stdout.strip(): return {}
        return json.loads(process.stdout)
    except json.JSONDecodeError:
        return {"status": "error", "message": f"Invalid JSON: {process.stdout}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Lỗi thực thi: {e.stderr or e.stdout}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ===== BƯỚC MỚI ĐÃ ĐƯỢC KHÔI PHỤC =====
def step_filter_files(file_list, min_size_mb):
    """Lọc và loại bỏ các file nhỏ hơn dung lượng tối thiểu cho phép."""
    if not min_size_mb or min_size_mb <= 0:
        return file_list
    
    print(f"\n[BƯỚC LỌC FILE] Lọc các file nhỏ hơn {min_size_mb}MB...")
    min_size_bytes = min_size_mb * 1024 * 1024
    
    filtered_list = []
    for f in file_list:
        try:
            if os.path.getsize(f) >= min_size_bytes:
                filtered_list.append(f)
            else:
                print(f" -> Bỏ qua file rác/nhỏ: {os.path.basename(f)}")
        except FileNotFoundError:
            # Bỏ qua nếu file không còn tồn tại
            continue
            
    return filtered_list

# --- CÁC BƯỚC XỬ LÝ TRONG PIPELINE ---

def step_rename_files(files_to_rename, base_name):
    """Gọi renamer.py để đổi tên các file."""
    if not files_to_rename: return []
    print(f"\n[BƯỚC ĐỔI TÊN] Đổi tên {len(files_to_rename)} file theo '{base_name}'...")
    cmd = ['python3', 'core/renamer.py', '--files-json', json.dumps(files_to_rename), '--base-name', base_name]
    result = run_module(cmd)
    if isinstance(result, list):
        print(" -> Đổi tên thành công.")
        return result
    else:
        print(f" -> Đổi tên thất bại: {result.get('message')}")
        return []

# ... (Các hàm step_join_files, step_split_files, step_upload_files, step_store_files giữ nguyên như phiên bản trước) ...
def step_join_files(file_list, output_name):
    if len(file_list) < 2: return file_list
    print(f"\n[BƯỚC NỐI FILE] Nối {len(file_list)} file thành '{output_name}'...")
    output_dir = os.path.dirname(file_list[0])
    _, ext = os.path.splitext(file_list[0])
    output_path = os.path.join(output_dir, output_name + ext)
    cmd = ['python3', 'core/joiner.py', '--files-json', json.dumps(sorted(file_list)), '--output-file', output_path, '--delete-parts']
    result = run_module(cmd)
    if result.get('status') == 'success': return [result.get('output_path')]
    print(f" -> Nối file thất bại: {result.get('message')}"); return []
def step_split_files(file_list, max_gb, split_times):
    final_files = []
    if split_times:
        print(f"\n[BƯỚC CHIA FILE] Chế độ thủ công theo các mốc thời gian: {split_times}")
        if len(file_list) > 1: print(" -> Cảnh báo: Chế độ chia thủ công chỉ áp dụng cho file đầu tiên.")
        file_to_split = file_list[0]
        cmd = ['python3', 'core/ffmpeg_splitter.py', '--file-path', file_to_split, '--start-times'] + [str(t) for t in split_times]
        result = run_module(cmd)
        if result.get('status') == 'manual_split': final_files.extend(result.get('files', []))
        else: print(f" -> Chia file thủ công thất bại cho: {os.path.basename(file_to_split)}.")
        final_files.extend(file_list[1:])
    elif max_gb and max_gb > 0:
        print(f"\n[BƯỚC CHIA FILE] Chế độ tự động, chia các file lớn hơn {max_gb}GB...")
        for f in file_list:
            cmd = ['python3', 'core/ffmpeg_splitter.py', '--file-path', f, '--max-size-gb', str(max_gb)]
            result = run_module(cmd)
            if result.get('status') in ['auto_split', 'unsplit']: final_files.extend(result.get('files', []))
            else: print(f" -> Chia file tự động thất bại cho {os.path.basename(f)}. Bỏ qua.")
    else: return file_list
    return final_files
def uploader_task(host, file_path, creds, excel_config):
    print(f" -> Bắt đầu upload {os.path.basename(file_path)} lên {host}...")
    uploader_script = f"uploaders/{host}_uploader.py"
    if not os.path.exists(uploader_script): print(f"Lỗi: Không tìm thấy script uploader: {uploader_script}"); return
    command = ['python3', uploader_script, '-f', file_path]
    for key, value in creds.items():
        if value: command.extend([f'--{key}', str(value)])
    upload_result = run_module(command)
    if excel_config and upload_result.get('status') == 'success':
        link_data = {"Name": os.path.basename(file_path), "Link": upload_result.get('upload_url'), "Host": f"{host}.com"}
        print(f" -> Ghi link vào Excel: {link_data['Name']}")
        excel_handler.write_row(excel_config['excel_file'], 'Host_Storage', 'Host_Storage', link_data)
def step_upload_files(file_list, upload_hosts, excel_config):
    if not upload_hosts or not file_list: return
    print(f"\n[BƯỚC UPLOAD] Bắt đầu upload lên: {', '.join(upload_hosts)}...")
    threads = []
    for host in upload_hosts:
        creds = config_manager.get_account_creds(host)
        if not creds: print(f"Cảnh báo: Không có tài khoản cho '{host}' trong accounts.ini. Bỏ qua."); continue
        for f in file_list:
            thread = threading.Thread(target=uploader_task, args=(host, f, creds, excel_config))
            threads.append(thread)
            thread.start()
    for t in threads: t.join()
def step_store_files(file_list, save_dir):
    if not file_list: return
    print(f"\n[BƯỚC LƯU TRỮ] Di chuyển {len(file_list)} file đến: {save_dir}")
    os.makedirs(save_dir, exist_ok=True)
    for f in file_list:
        if os.path.exists(f):
            try: shutil.move(f, os.path.join(save_dir, os.path.basename(f)))
            except Exception as e: print(f" -> Lỗi khi di chuyển {os.path.basename(f)}: {e}")
def find_torrent_file(torrent_dir, task_name):
    if not os.path.isdir(torrent_dir): return None
    for filename in os.listdir(torrent_dir):
        if task_name in filename and filename.endswith('.torrent'):
            return os.path.join(torrent_dir, filename)
    return None

# --- WORKFLOWS ---

def workflow_download(args, config):
    """Quy trình tổng quát cho việc tải file."""
    # ... (phần code đọc excel giữ nguyên) ...
    sheet_map = {'url-download': 'DownLoadUrl', 'magnet-download': 'DownLoadMagnetLink', 'torrent-download': 'DownLoadTorrent'}
    sheet_name = sheet_map[args.workflow]
    tasks = excel_handler.read_table(config['excel_file'], sheet_name, sheet_name)
    if not tasks: print(f"Không có tác vụ trong sheet '{sheet_name}'."); return
    pending_tasks = [t for t in tasks if str(t.get('Downloaded', '')).lower() != 'downloaded']
    print(f"Tìm thấy {len(pending_tasks)} tác vụ cần xử lý.")

    for i, task in enumerate(pending_tasks):
        task_name = task.get('Name')
        if not task_name: print(f"Bỏ qua tác vụ dòng {i+2} vì thiếu 'Name'."); continue
        print(f"\n--- Bắt đầu xử lý tác vụ {i+1}/{len(pending_tasks)}: {task_name} ---")
        
        # 1. Tải file (logic giữ nguyên)
        downloader_script = f"downloaders/{args.workflow.split('-')[0]}_downloader.py"
        cmd_download = ['python3', downloader_script, '-o', config['download_dir']]
        link=None
        if args.workflow == 'url-download':
            link = task.get('Url'); cmd_download.extend(['-u', link, '-n', task_name])
        elif args.workflow == 'magnet-download':
            link = task.get('MagnetLink'); cmd_download.extend(['-m', link])
        elif args.workflow == 'torrent-download':
            link = find_torrent_file(config['torrent_dir'], task_name); cmd_download.extend(['-t', link])
        if not link: print(f"Lỗi: Tác vụ '{task_name}' thiếu link."); continue
        
        download_result = run_module(cmd_download)
        if download_result.get('status') != 'success': print(f" -> Tải về thất bại."); continue
        
        newly_downloaded_files = download_result.get('files', [])
        if not newly_downloaded_files: print(" -> Downloader không trả về file nào."); continue

        # ===== 2. LỌC FILE (BƯỚC ĐÃ KHÔI PHỤC) =====
        filtered_files = step_filter_files(newly_downloaded_files, args.min_size_mb)
        if not filtered_files:
            print(" -> Không còn file nào sau khi lọc. Bỏ qua tác vụ.")
            continue

        # 3. Đổi tên file
        renamed_files = step_rename_files(filtered_files, task_name)
        if not renamed_files: print(" -> Dừng tác vụ do đổi tên thất bại."); continue

        # 4. Xử lý pipeline (nối, chia)
        processed_files = renamed_files
        if args.join_files: processed_files = step_join_files(processed_files, task_name)
        processed_files = step_split_files(processed_files, args.split_max_gb, args.split_at_times)
        
        # 5. Upload và Lưu trữ
        step_upload_files(processed_files, args.uploaders, config)
        step_store_files(processed_files, config['save_dir'])

        # 6. Cập nhật Excel
        excel_handler.update_cell(config['excel_file'], sheet_name, sheet_name, tasks.index(task), 'Downloaded', 'downloaded')
        print(f"--- Hoàn thành tác vụ: {task_name} ---")

def workflow_process_local(args, config):
    """Quy trình xử lý các file có sẵn trong thư mục."""
    if not os.path.isdir(args.source_dir): print("Lỗi: --source-dir không hợp lệ."); return
    if not args.output_name: print("Lỗi: --output-name là bắt buộc."); return

    initial_files = [os.path.join(args.source_dir, f) for f in os.listdir(args.source_dir) if os.path.isfile(os.path.join(args.source_dir, f))]
    if not initial_files: print(f"Không tìm thấy file trong {args.source_dir}."); return

    # ===== LỌC FILE (BƯỚC ĐÃ KHÔI PHỤC) =====
    filtered_files = step_filter_files(initial_files, args.min_size_mb)
    if not filtered_files:
        print("Không còn file nào sau khi lọc. Dừng quy trình.")
        return

    renamed_files = step_rename_files(filtered_files, args.output_name)
    if not renamed_files: print("Dừng do đổi tên thất bại."); return

    processed_files = renamed_files
    if args.join_files: processed_files = step_join_files(processed_files, args.output_name)
    processed_files = step_split_files(processed_files, args.split_max_gb, args.split_at_times)

    step_upload_files(processed_files, args.uploaders, config)
    step_store_files(processed_files, config['save_dir'])
    print("\nQuy trình 'process-local' đã hoàn tất!")

# ... (workflow_upload_local giữ nguyên) ...
def workflow_upload_local(args, config):
    if not args.uploaders: print("Lỗi: --uploaders là bắt buộc."); return
    for host in args.uploaders:
        print(f"\n--- Tìm file cần upload cho host: {host}.com ---")
        files_to_upload = file_utils.find_files_to_upload(config['save_dir'], config['excel_file'], 'Host_Storage', 'Host_Storage', f"{host}.com")
        if not files_to_upload: print(f" -> Không có file mới nào cần upload cho {host}.com."); continue
        print(f" -> Tìm thấy {len(files_to_upload)} file.");
        step_upload_files(files_to_upload, [host], config)
    print("\nQuy trình 'upload-local' đã hoàn tất!")


# --- HÀM MAIN CHÍNH ---
def main():
    parser = argparse.ArgumentParser(description="Công cụ tự động hóa xử lý và upload file.", formatter_class=argparse.RawTextHelpFormatter)
    
    req_args = parser.add_argument_group('Tham số bắt buộc')
    req_args.add_argument("-c", "--category", required=True, help="Tên danh mục trong config.ini.")
    req_args.add_argument("-w", "--workflow", required=True, choices=['url-download', 'torrent-download', 'magnet-download', 'process-local', 'upload-local'], help="Quy trình cần chạy.")
    
    opt_args = parser.add_argument_group('Tham số tùy chọn')
    # ===== THAM SỐ ĐÃ ĐƯỢC KHÔI PHỤC =====
    opt_args.add_argument("--min-size-mb", type=int, default=10, help="Lọc và bỏ qua các file nhỏ hơn dung lượng này (MB). Mặc định: 10MB.")
    opt_args.add_argument("--source-dir", help="Thư mục nguồn cho workflow 'process-local'.")
    opt_args.add_argument("--output-name", help="Tên file output mong muốn cho 'process-local'.")
    opt_args.add_argument("--join-files", action='store_true', help="Bật tính năng nối các file thành một.")
    opt_args.add_argument("--split-max-gb", type=int, help="CHẾ ĐỘ TỰ ĐỘNG: Chia file theo dung lượng (GB).")
    opt_args.add_argument("--split-at-times", nargs='+', type=float, help="CHẾ ĐỘ THỦ CÔNG: Chia file theo các mốc thời gian (giây).")
    opt_args.add_argument("-up", "--uploaders", nargs='+', help="Danh sách host để upload (vd: nitroflare keep2share).")
    
    args = parser.parse_args()
    
    config = config_manager.get_category_config(args.category)
    if not config: print(f"Lỗi: Không có cấu hình cho '{args.category}'."); return
    
    workflows = {
        'url-download': workflow_download, 'torrent-download': workflow_download, 'magnet-download': workflow_download,
        'process-local': workflow_process_local, 'upload-local': workflow_upload_local
    }
    workflows[args.workflow](args, config)

if __name__ == '__main__':
    main()
