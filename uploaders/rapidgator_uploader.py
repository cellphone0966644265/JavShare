# /uploaders/rapidgator_uploader.py
import argparse
import json
import os
import subprocess
import time

def run_curl(cmd):
    """Hàm phụ để chạy lệnh curl và trả về stdout."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, output=result.stdout, stderr=result.stderr)
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description="Tải file lên Rapidgator.")
    parser.add_argument("-f", "--file", required=True, help="Đường dẫn file cần upload.")
    parser.add_argument("--username", required=True, help="Tên đăng nhập Rapidgator.")
    parser.add_argument("--password", required=True, help="Mật khẩu Rapidgator.")
    args = parser.parse_args()

    try:
        if not os.path.exists(args.file):
            raise FileNotFoundError(f"File không tồn tại: {args.file}")

        # 1. Lấy token
        login_cmd = ['curl', '-s', '-X', 'POST', 'https://rapidgator.net/api/v2/user/login', '-d', f'login={args.username}', '-d', f'password={args.password}']
        login_response = json.loads(run_curl(login_cmd))
        token = login_response.get('response', {}).get('token')
        if not token:
            raise ValueError("Lấy access token thất bại.")

        # 2. Lấy URL để upload
        file_name = os.path.basename(args.file)
        get_url_cmd = ['curl', '-s', '-G', 'https://rapidgator.net/api/v2/file/upload', '--data-urlencode', f'token={token}', '--data-urlencode', f'name={file_name}']
        upload_info_response = json.loads(run_curl(get_url_cmd))
        upload_url = upload_info_response.get('response', {}).get('url')
        if not upload_url:
            raise ValueError(f"Lấy upload URL thất bại: {upload_info_response}")

        # 3. Upload file
        upload_cmd = ['curl', '-s', '-X', 'POST', upload_url, '-F', f'file=@{args.file}']
        upload_response = json.loads(run_curl(upload_cmd))
        file_id = upload_response.get('response', {}).get('file', {}).get('id')
        if not file_id:
             raise RuntimeError(f"Upload file thất bại: {upload_response}")

        # 4. Trả về kết quả thành công với link file
        file_link = f"https://rapidgator.net/file/{file_id}"
        result = {"status": "success", "upload_url": file_link}
        print(json.dumps(result, indent=4))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=4))
        exit(1)

if __name__ == '__main__':
    main()
