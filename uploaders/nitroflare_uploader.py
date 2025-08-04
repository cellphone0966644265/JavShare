# /uploaders/nitroflare_uploader.py

import argparse
import json
import os
import subprocess

def main():
    """Hàm chính để tải file lên Nitroflare."""
    parser = argparse.ArgumentParser(description="Tải một file lên Nitroflare và trả về kết quả JSON.")
    parser.add_argument("-f", "--file", required=True, help="Đường dẫn đến file cần upload.")
    parser.add_argument("-uh", "--user-hash", required=True, help="User hash của tài khoản Nitroflare.")
    
    args = parser.parse_args()
    
    try:
        if not os.path.exists(args.file):
            raise FileNotFoundError(f"File không tồn tại: {args.file}")

        # Bước 1: Lấy địa chỉ server upload của Nitroflare
        get_server_cmd = ['curl', 'http://nitroflare.com/plugins/fileupload/getServer']
        server_process = subprocess.run(get_server_cmd, capture_output=True, text=True, check=True)
        server_url = server_process.stdout.strip()
        
        if not server_url:
            raise ConnectionError("Không lấy được địa chỉ server upload từ Nitroflare.")

        # Bước 2: Upload file lên server đó bằng curl
        file_arg = f"files=@{args.file}"
        user_arg = f"user={args.user_hash}"
        upload_cmd = ['curl', '-F', user_arg, '-F', file_arg, server_url]
        
        upload_process = subprocess.run(upload_cmd, capture_output=True, text=True, check=True)
        
        # Phân tích kết quả JSON trả về từ Nitroflare
        response_json = json.loads(upload_process.stdout)
        
        if 'files' in response_json and len(response_json['files']) > 0:
            file_info = response_json['files'][0]
            if 'url' in file_info:
                upload_url = file_info['url'].replace('\\/', '/')
                result = {
                    "status": "success",
                    "file_path": args.file,
                    "upload_url": upload_url
                }
                print(json.dumps(result, indent=4))
            else:
                raise ValueError(f"Kết quả trả về không chứa URL: {upload_process.stdout}")
        else:
            raise ValueError(f"Upload thất bại hoặc kết quả trả về không hợp lệ: {upload_process.stdout}")

    except subprocess.CalledProcessError as e:
        error_message = {
            "status": "error",
            "message": "Lệnh curl thất bại.",
            "stderr": e.stderr.strip()
        }
        print(json.dumps(error_message, indent=4))
        exit(1)
    except Exception as e:
        error_message = {"status": "error", "message": str(e)}
        print(json.dumps(error_message, indent=4))
        exit(1)

if __name__ == '__main__':
    main()
