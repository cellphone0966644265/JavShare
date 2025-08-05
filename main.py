# /main.py
import argparse
import json
import os
import subprocess
import threading
import shutil
from core import config_manager, excel_handler, file_utils

# --- CÁC HÀM TIỆN ÍCH (Không đổi) ---
def run_module(command_args):
    try:
        process = subprocess.run(command_args, capture_output=True, text=True, check=True, encoding='utf-8')
        if not process.stdout.strip(): return {}
        return json.loads(process.stdout)
    except json.JSONDecodeError:
        return {"status": "error", "message": f"Invalid JSON: {process.stdout}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Lỗi thực thi: {e.stderr or e.stdout}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def step_filter_files(file_list, min_size_mb):
    if not min_size_mb or min_size_mb <= 0: return file_list
    print(f"\n[BƯỚC LỌC FILE] Lọc các file nhỏ hơn {min_size_mb}MB...")
    min_size_bytes = min_size_mb * 1024 * 1024
    filtered_list = [f for f in file_list if os.path.exists(f) and os.path.getsize(f) >= min_size_bytes]
    removed_count = len(file_list) - len(filtered_list)
    if removed_count > 0: print(f" -> Đã loại bỏ {removed_count} file nhỏ.")
    return filtered_list

def step_rename_files(files_to_rename, base_name):
    if not files_to_rename: return []
    print(f"\n[BƯỚC ĐỔI TÊN] Đổi tên {len(files_to_rename)} file theo '{base_name}'...")
    cmd = ['python3', 'core/renamer.py', '--files-json', json.dumps(files_to_rename), '--base-name', base_name]
    result = run_module(cmd)
    if isinstance(result, list):
        print(" -> Đổi tên thành công.")
        return result
    else:
        print(f" -> Đổi tên thất bại: {result.get('message')}"); return []

def step_upload_files(file_list, upload_hosts, excel_config):
    if not upload_hosts or not file_list: return
    print(f"\n[BƯỚC UPLOAD] Bắt đầu upload lên: {', '.join(upload_hosts)}...")
    threads = []
    for host in upload_hosts:
        creds = config_manager.get_account_creds(host)
        if not creds: print(f"Cảnh báo: Không có tài khoản cho '{host}'. Bỏ qua."); continue
        for f in file_list:
            thread = threading.Thread(target=uploader_task, args=(host, f, creds, excel_config))
            threads.append(thread)
            thread.start()
    for t in threads: t.join()

def uploader_task(host, file_path, creds, excel_config):
    print(f" -> Bắt đầu upload {os.path.basename(file_path)} lên {host}...")
    uploader_script = f"uploaders/{host}_uploader.py"
    if not os.path.exists(uploader_script): print(f"Lỗi: Không tìm thấy script: {uploader_script}"); return
    command = ['python3', uploader_script, '-f', file_path]
    for key, value in creds.items():
        if value: command.extend([f'--{key}', str(value)])
    upload_result = run_module(command)
    if excel_config and upload_result.get('status') == 'success':
        link_data = {"Name": os.path.basename(file_path), "Link": upload_result.get('upload_url'), "Host": f"{host}.com"}
        print(f" -> Ghi link vào Excel: {link_data['Name']}")
        excel_handler.write_row(excel_config['excel_file'], 'Host_Storage', 'Host_Storage', link_data)

def step_store_files(file_list, save_dir):
    if not file_list: return
    print(f"\n[BƯỚC LƯU TRỮ] Di chuyển {len(file_list)} file đến: {save_dir}")
    os.makedirs(save_dir, exist_ok=True)
    for f in file_list:
        if os.path.exists(f):
            try: shutil.move(f, os.path.join(save_dir, os.path.basename(f)))
            except Exception as e: print(f" -> Lỗi khi di chuyển {os.path.basename(f)}: {e}")

# --- WORKFLOWS ĐÃ ĐƯỢC TÁCH RIÊNG ---

# ===== WORKFLOW CHO URL VÀ MAGNET (ĐỌC EXCEL TRƯỚC) =====
def workflow_url_magnet_download(args, config):
    sheet_map = {'url-download': 'DownLoadUrl', 'magnet-download': 'DownLoadMagnetLink'}
    sheet_name = sheet_map[args.workflow]
    tasks = excel_handler.read_table(config['excel_file'], sheet_name, sheet_name)
    if not tasks: print(f"Không có tác vụ trong sheet '{sheet_name}'."); return
    
    pending_tasks = [t for t in tasks if str(t.get('Downloaded', '')).lower() != 'downloaded']
    print(f"Tìm thấy {len(pending_tasks)} tác vụ cần xử lý từ Excel.")

    for i, task in enumerate(pending_tasks):
        task_name = task.get('Name')
        if not task_name: print(f"Bỏ qua tác vụ dòng {i+2} vì thiếu 'Name'."); continue
        print(f"\n--- Bắt đầu xử lý tác vụ {i+1}/{len(pending_tasks)}: {task_name} ---")
        
        downloader_script = f"downloaders/{args.workflow.split('-')[0]}_downloader.py"
        cmd_download = ['python3', downloader_script, '-o', config['download_dir']]
        link = task.get('Url') or task.get('MagnetLink')
        if not link: print(f"Lỗi: Tác vụ '{task_name}' thiếu link."); continue
        
        if args.workflow == 'url-download': cmd_download.extend(['-u', link, '-n', task_name])
        else: cmd_download.extend(['-m', link])
        
        download_result = run_module(cmd_download)
        if download_result.get('status') != 'success': print(f" -> Tải về thất bại."); continue
        
        newly_downloaded_files = download_result.get('files', [])
        if not newly_downloaded_files: print(" -> Downloader không trả về file nào."); continue

        filtered_files = step_filter_files(newly_downloaded_files, args.min_size_mb)
        if not filtered_files: print(" -> Không còn file nào sau khi lọc."); continue

        renamed_files = step_rename_files(filtered_files, task_name)
        if not renamed_files: print(" -> Dừng tác vụ do đổi tên thất bại."); continue
        
        # Các bước xử lý sau không đổi
        step_upload_files(renamed_files, args.uploaders, config)
        step_store_files(renamed_files, config['save_dir'])
        excel_handler.update_cell(config['excel_file'], sheet_name, sheet_name, tasks.index(task), 'Downloaded', 'downloaded')
        print(f"--- Hoàn thành tác vụ: {task_name} ---")

# ===== WORKFLOW CHO TORRENT (DUYỆT THƯ MỤC TRƯỚC - THEO ĐÚNG LOGIC GỐC CỦA BẠN) =====
def workflow_torrent_download(args, config):
    torrent_dir = config['torrent_dir']
    if not os.path.isdir(torrent_dir):
        print(f"Lỗi: Thư mục torrent '{torrent_dir}' không tồn tại."); return

    torrent_files = [f for f in os.listdir(torrent_dir) if f.endswith('.torrent')]
    if not torrent_files:
        print(f"Không tìm thấy file .torrent nào trong '{torrent_dir}'."); return
        
    print(f"Tìm thấy {len(torrent_files)} file .torrent để xử lý.")

    for i, torrent_filename in enumerate(sorted(torrent_files)):
        print(f"\n--- Bắt đầu xử lý file {i+1}/{len(torrent_files)}: {torrent_filename} ---")
        torrent_path = os.path.join(torrent_dir, torrent_filename)

        # 1. Tải file
        cmd_download = ['python3', 'downloaders/torrent_downloader.py', '-t', torrent_path, '-o', config['download_dir']]
        download_result = run_module(cmd_download)
        if download_result.get('status') != 'success':
            print(f" -> Tải torrent thất bại: {download_result.get('message')}"); continue

        newly_downloaded_files = download_result.get('files', [])
        if not newly_downloaded_files:
            print(" -> Downloader không trả về file nào."); continue

        # 2. Lọc file rác
        filtered_files = step_filter_files(newly_downloaded_files, args.min_size_mb)
        if not filtered_files:
            print(" -> Không còn file nào sau khi lọc."); continue

        # 3. Đổi tên file theo tên file torrent (không có phần mở rộng)
        base_name, _ = os.path.splitext(torrent_filename)
        renamed_files = step_rename_files(filtered_files, base_name)
        if not renamed_files:
            print(" -> Dừng xử lý file này do đổi tên thất bại."); continue

        # 4. Upload (sẽ tự ghi vào sheet Host_Storage) và Lưu trữ
        step_upload_files(renamed_files, args.uploaders, config)
        step_store_files(renamed_files, config['save_dir'])

        # 5. Di chuyển file .torrent đã xử lý sang thư mục 'Downloaded'
        dest_path = os.path.join(config['torrent_downloaded_dir'], torrent_filename)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.move(torrent_path, dest_path)
        print(f" -> Đã di chuyển {torrent_filename} sang thư mục đã xử lý.")
        print(f"--- Hoàn thành xử lý: {torrent_filename} ---")
        
# --- Các workflow khác (không đổi) ---
def workflow_process_local(args, config):
    # ...
def workflow_upload_local(args, config):
    # ...

# --- HÀM MAIN CHÍNH (Đã cập nhật để gọi đúng workflow) ---
def main():
    # ... (Phần parser không đổi) ...
    parser = argparse.ArgumentParser(description="Công cụ tự động hóa xử lý và upload file.", formatter_class=argparse.RawTextHelpFormatter)
    req_args = parser.add_argument_group('Tham số bắt buộc')
    req_args.add_argument("-c", "--category", required=True, help="Tên danh mục trong config.ini.")
    req_args.add_argument("-w", "--workflow", required=True, choices=['url-download', 'torrent-download', 'magnet-download', 'process-local', 'upload-local'], help="Quy trình cần chạy.")
    opt_args = parser.add_argument_group('Tham số tùy chọn')
    opt_args.add_argument("--min-size-mb", type=int, default=10, help="Lọc file nhỏ hơn dung lượng này (MB).")
    #... các args khác
    args = parser.parse_args()

    config = config_manager.get_category_config(args.category)
    if not config:
        print(f"Lỗi: Không có cấu hình cho '{args.category}'."); return
    
    # ===== BỘ ĐIỀU PHỐI WORKFLOW ĐÃ CẬP NHẬT =====
    if args.workflow in ['url-download', 'magnet-download']:
        workflow_url_magnet_download(args, config)
    elif args.workflow == 'torrent-download':
        workflow_torrent_download(args, config)
    elif args.workflow == 'process-local':
        workflow_process_local(args, config)
    elif args.workflow == 'upload-local':
        workflow_upload_local(args, config)

if __name__ == '__main__':
    main()
