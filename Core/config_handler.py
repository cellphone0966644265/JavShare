# /core/config_handler.py

import argparse
import json

def get_config(category_name):
    """
    Hàm này chứa toàn bộ cấu hình và trả về thông tin cho một danh mục cụ thể.
    """
    # BẠN CẦN THAY ĐỔI CÁC ĐƯỜNG DẪN BÊN DƯỚI CHO ĐÚNG VỚI MÁY CỦA BẠN
    CONFIG = {
        'Censored': {
            'excel_file': '/home/nha/JavShare/Censored/Link/Censored.xlsx',
            'download_dir': '/home/nha/JavShare/Censored/Download/',
            'save_dir': '/home/nha/JavShare/Censored/Video/',
            'torrent_dir': '/home/nha/JavShare/Censored/Link/Torrent/UnDownloaded'
        },
        'Demosaic': {
            'excel_file': '/home/nha/JavShare/Demosaic/Link/Demosaic.xlsx',
            'download_dir': '/home/nha/JavShare/Demosaic/Download/',
            'save_dir': '/home/nha/JavShare/Demosaic/Video/',
            'torrent_dir': '/home/nha/JavShare/Demosaic/Link/Torrent/UnDownloaded'
        },
        'Uncensored': {
            'excel_file': '/home/nha/JavShare/Uncensored/Link/Uncensored.xlsx',
            'download_dir': '/home/nha/JavShare/Uncensored/Download/',
            'save_dir': '/home/nha/JavShare/Uncensored/Video/',
            'torrent_dir': '/home/nha/JavShare/Uncensored/Link/Torrent/UnDownloaded'
        },
        'VrCensored': {
            'excel_file': '/home/nha/JavShare/VrCensored/Link/VrCensored.xlsx',
            'download_dir': '/home/nha/JavShare/VrCensored/Download/',
            'save_dir': '/home/nha/JavShare/VrCensored/Video/',
            'torrent_dir': '/home/nha/JavShare/VrCensored/Link/Torrent/UnDownloaded'
        },
        'VrDemosaic': {
            'excel_file': '/home/nha/JavShare/VrDemosaic/Link/VrDemosaic.xlsx',
            'download_dir': '/home/nha/JavShare/VrDemosaic/Download/',
            'save_dir': '/home/nha/JavShare/VrDemosaic/Video/',
            'torrent_dir': '/home/nha/JavShare/VrDemosaic/Link/Torrent/UnDownloaded'
        },
        'VrUncensored': {
            'excel_file': '/home/nha/JavShare/VrUncensored/Link/VrUncensored.xlsx',
            'download_dir': '/home/nha/JavShare/VrUncensored/Download/',
            'save_dir': '/home/nha/JavShare/VrUncensored/Video/',
            'torrent_dir': '/home/nha/JavShare/VrUncensored/Link/Torrent/UnDownloaded'
        }
    }
    
    config_data = CONFIG.get(category_name)
    if not config_data:
        raise ValueError(f"Không tìm thấy danh mục cấu hình: '{category_name}'")
    
    return config_data

def main():
    """Hàm chính điều phối từ dòng lệnh."""
    parser = argparse.ArgumentParser(description="Lấy thông tin cấu hình cho một danh mục.")
    parser.add_argument("-c", "--category", required=True, help="Tên danh mục cần lấy cấu hình (ví dụ: VrCensored).")
    args = parser.parse_args()
    
    try:
        config_data = get_config(args.category)
        # Trả về kết quả dạng JSON
        print(json.dumps(config_data, indent=4))
    except Exception as e:
        # Trả về lỗi dạng JSON
        print(json.dumps({"status": "error", "message": str(e)}, indent=4))
        exit(1)

if __name__ == '__main__':
    main()
