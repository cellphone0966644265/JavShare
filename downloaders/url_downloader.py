# /downloaders/url_downloader.py

import requests
import argparse
import json
import os
from tqdm import tqdm

def main():
    """Hàm chính để tải file từ URL."""
    parser = argparse.ArgumentParser(description="Tải file từ một URL và trả về kết quả JSON.")
    parser.add_argument("-u", "--url", required=True, help="URL của file cần tải.")
    parser.add_argument("-o", "--output-dir", required=True, help="Thư mục để lưu file.")
    parser.add_argument("-n", "--filename", required=True, help="Tên file để lưu.")
    
    args = parser.parse_args()
    
    output_path = os.path.join(args.output_dir, args.filename)
    
    try:
        # Tạo thư mục nếu nó không tồn tại
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Gửi yêu cầu tới URL
        response = requests.get(args.url, stream=True)
        response.raise_for_status()  # Báo lỗi nếu URL không hợp lệ (lỗi 4xx hoặc 5xx)

        # Lấy tổng dung lượng file
        total_size = int(response.headers.get('content-length', 0))
        
        # Bắt đầu tải file với thanh tiến trình
        with open(output_path, 'wb') as f, tqdm(
            desc=args.filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                bar.update(size)

        # Lấy dung lượng file thực tế sau khi tải
        final_size = os.path.getsize(output_path)
        
        result = {
            "status": "success",
            "file_path": output_path,
            "size_bytes": final_size
        }
        print(json.dumps(result, indent=4))

    except Exception as e:
        # Xóa file tải dở nếu có lỗi
        if os.path.exists(output_path):
            os.remove(output_path)
            
        error_message = {"status": "error", "message": str(e)}
        print(json.dumps(error_message, indent=4))
        exit(1)

if __name__ == '__main__':
    main()
