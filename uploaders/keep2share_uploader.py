# /uploaders/keep2share_uploader.py
import argparse
import json
import os
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Tải file lên Keep2Share.")
    parser.add_argument("-f", "--file", required=True, help="Đường dẫn file cần upload.")
    parser.add_argument("--access_token", required=True, help="Access token của tài khoản Keep2Share.")
    args = parser.parse_args()
    
    try:
        if not os.path.exists(args.file):
            raise FileNotFoundError(f"File không tồn tại: {args.file}")

        get_form_url = "https://k2s.cc/api/v2/getUploadFormData"
        form_payload = json.dumps({"access_token": args.access_token})
        form_cmd = ['curl', '-s', '-X', 'POST', '-H', 'Content-type: application/json', '-d', form_payload, get_form_url]
        form_data = json.loads(subprocess.run(form_cmd, capture_output=True, text=True, check=True).stdout)

        form_action = form_data.get('form_action')
        file_field = form_data.get('file_field')
        if not form_action or not file_field:
            raise ValueError(f"Không lấy được form upload: {form_data}")

        upload_cmd = ['curl', '-s']
        for key, value in form_data.get('form_data', {}).items():
            upload_cmd.extend(['-F', f'{key}={value}'])
        upload_cmd.extend(['-F', f'{file_field}=@{args.file}'])
        upload_cmd.append(form_action)
        
        upload_response = json.loads(subprocess.run(upload_cmd, capture_output=True, text=True, check=True).stdout)
        
        if upload_response.get('status') == 'success':
            result = {"status": "success", "upload_url": upload_response.get('link')}
            print(json.dumps(result, indent=4))
        else:
            raise RuntimeError(f"Upload thất bại: {upload_response}")

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=4))
        exit(1)

if __name__ == '__main__':
    main()
