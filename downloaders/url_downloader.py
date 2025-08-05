# /downloaders/url_downloader.py
import requests
import argparse
import json
import os
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description="Tải file từ một URL.")
    parser.add_argument("-u", "--url", required=True, help="URL của file cần tải.")
    parser.add_argument("-o", "--output-dir", required=True, help="Thư mục để lưu file.")
    parser.add_argument("-n", "--filename", required=True, help="Tên file để lưu.")
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, args.filename)
    
    try:
        response = requests.get(args.url, stream=True)
        response.raise_for_status() 

        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f, tqdm(
            desc=args.filename, total=total_size, unit='iB', unit_scale=True, unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                bar.update(size)

        result = {"status": "success", "files": [output_path]}
        print(json.dumps(result, indent=4))

    except Exception as e:
        if os.path.exists(output_path): os.remove(output_path)
        print(json.dumps({"status": "error", "message": str(e)}, indent=4))
        exit(1)

if __name__ == '__main__':
    main()
