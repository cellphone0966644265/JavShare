# /core/account.py

import configparser
import os
import argparse
import json

def main():
    """
    Hàm chính để thực thi logic của script.
    """
    # --- ĐẦU VÀO: Định nghĩa và lấy tham số từ dòng lệnh ---
    parser = argparse.ArgumentParser(
        description="Lấy thông tin tài khoản từ file và trả về dưới dạng JSON.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-f", "--file",
        required=True,
        help="Đường dẫn đến file account.txt."
    )
    parser.add_argument(
        "-s", "--service",
        required=True,
        help="Tên dịch vụ cần lấy tài khoản (ví dụ: 'rapidgator')."
    )
    args = parser.parse_args()

    # --- XỬ LÝ: Logic chính của module ---
    try:
        if not os.path.exists(args.file):
            raise FileNotFoundError(f"File tài khoản không tồn tại: {args.file}")

        config = configparser.ConfigParser()
        config.read(args.file)

        service_name = args.service.lower()
        if service_name in config:
            credentials = dict(config[service_name])
            # --- ĐẦU RA: Trả về kết quả bằng cách in ra JSON ---
            print(json.dumps(credentials, indent=4))
        else:
            raise ValueError(f"Không tìm thấy dịch vụ '{args.service}' trong file.")

    except Exception as e:
        # --- XỬ LÝ LỖI: Trả về lỗi dưới dạng JSON ---
        error_message = {"error": str(e)}
        print(json.dumps(error_message, indent=4))
        exit(1) # Thoát với mã lỗi

if __name__ == '__main__':
    main()
