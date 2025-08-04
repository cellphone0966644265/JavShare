# /uploaders/keep2share_uploader.py

import argparse
import json
import os
import subprocess

def main():
    """Hàm chính để tải file lên Keep2Share bằng access_token."""
    parser = argparse.ArgumentParser(description="Tải một file lên Keep2Share bằng access_token và trả về kết quả JSON.")
    parser.add_argument("-f", "--file", required=True, help="Đường dẫn đến file cần upload.")
    parser.add_argument("-t", "--access-token", required=True, help="Access token của tài khoản Keep2Share.")
    
    args = parser.parse_args()
    
    base_api_url = "https://k2s.cc/api/v2"

    try:
        if not os.path.exists(args.file):
            raise FileNotFoundError(f"File không tồn tại: {args.file}")

        # Bước 1: Lấy thông tin form upload (Sử dụng trực tiếp token được cung cấp)
        get_form_url = f"{base_api_url}/getUploadFormData"
        form_payload = json.dumps({"access_token": args.access_token})
        form_cmd = [
            'curl', '-s', '-X', 'POST',
            '-H', 'Content-type: application/json',
            '-d', form_payload,
            get_form_url
        ]
        form_process = subprocess.run(form_cmd, capture_output=True, text=True, check=True)
        form_data = json.loads(form_process.stdout)

        form_action = form_data.get('form_action')
        file_field = form_data.get('file_field')
        form_details = form_data.get('form_data', {})

        if not form_action or not file_field:
            raise ValueError(f"Không lấy được thông tin form upload: {form_process.stdout}")

        # Bước 2: Upload file với đầy đủ các trường form
        upload_cmd = ['curl', '-s']
        for key, value in form_details.items():
            upload_cmd.extend(['-F', f'{key}={value}'])
        
        upload_cmd.extend(['-F', f'{file_field}=@{args.file}'])
        upload_cmd.append(form_action)
        
        upload_process = subprocess.run(upload_cmd, capture_output=True, text=True, check=True)
        upload_json_response = json.loads(upload_process.stdout)

        if upload_json_response.get('status') == 'success':
            final_link = upload_json_response.get('link')
            result = {
                "status": "success",
                "file_path": args.file,
                "upload_url": final_link
            }
            print(json.dumps(result, indent=4))
        else:
            raise RuntimeError(f"Upload thất bại: {upload_json_response}")

    except Exception as e:
        error_message = {"status": "error", "message": str(e)}
        print(json.dumps(error_message, indent=4))
        exit(1)

if __name__ == '__main__':
    main()
