# /uploaders/nitroflare_uploader.py
import argparse
import json
import os
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Tải file lên Nitroflare.")
    parser.add_argument("-f", "--file", required=True, help="Đường dẫn file cần upload.")
    parser.add_argument("--user_hash", required=True, help="User hash của tài khoản Nitroflare.")
    args = parser.parse_args()
    
    try:
        if not os.path.exists(args.file):
            raise FileNotFoundError(f"File không tồn tại: {args.file}")

        get_server_cmd = ['curl', '-s', 'http://nitroflare.com/plugins/fileupload/getServer']
        server_url = subprocess.run(get_server_cmd, capture_output=True, text=True, check=True).stdout.strip()
        if not server_url:
            raise ConnectionError("Không lấy được server upload từ Nitroflare.")

        upload_cmd = ['curl', '-s', '-F', f"user={args.user_hash}", '-F', f"files=@{args.file}", server_url]
        response_text = subprocess.run(upload_cmd, capture_output=True, text=True, check=True).stdout
        
        response_json = json.loads(response_text)
        file_info = response_json.get('files', [{}])[0]
        upload_url = file_info.get('url')

        if upload_url:
            result = {"status": "success", "upload_url": upload_url.replace('\\/', '/')}
            print(json.dumps(result, indent=4))
        else:
            raise ValueError(f"Upload thất bại hoặc kết quả không hợp lệ: {response_text}")

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=4))
        exit(1)

if __name__ == '__main__':
    main()
