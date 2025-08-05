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
            'excel_file': '/content/drive/MyDrive/Censored/Link/Censored.xlsx',
            'download_dir': '/content/drive/MyDrive/Censored/Download/',
            'save_dir': '/content/drive/MyDrive/Censored/Video/',
            'torrent_dir': '/content/drive/MyDrive/Censored/Link/Torrent/UnDownloaded',
            'torrent_downloaded_dir': '/content/drive/MyDrive/Censored/Link/Torrent/Downloaded'
        },
        'Demosaic': {
            'excel_file': '/content/drive/MyDrive/Demosaic/Link/Demosaic.xlsx',
            'download_dir': '/content/drive/MyDrive/Demosaic/Download/',
            'save_dir': '/content/drive/MyDrive/Demosaic/Video/',
            'torrent_dir': '/content/drive/MyDrive/Demosaic/Link/Torrent/UnDownloaded',
            'torrent_downloaded_dir': '/content/drive/MyDrive/Demosaic/Link/Torrent/Downloaded'
        },
        'Uncensored': {
            'excel_file': '/content/drive/MyDrive/Uncensored/Link/Uncensored.xlsx',
            'download_dir': '/content/drive/MyDrive/Uncensored/Download/',
            'save_dir': '/content/drive/MyDrive/Uncensored/Video/',
            'torrent_dir': '/content/drive/MyDrive/Uncensored/Link/Torrent/UnDownloaded',
            'torrent_downloaded_dir': '/content/drive/MyDrive/Uncensored/Link/Torrent/Downloaded'
        },
        'VrCensored': {
            'excel_file': '/content/drive/MyDrive/VrCensored/Link/VrCensored.xlsx',
            'download_dir': '/content/drive/MyDrive/VrCensored/Download/',
            'save_dir': '/content/drive/MyDrive/VrCensored/Video/',
            'torrent_dir': '/content/drive/MyDrive/VrCensored/Link/Torrent/UnDownloaded',
            'torrent_downloaded_dir': '/content/drive/MyDrive/VrCensored/Link/Torrent/Downloaded'
        },
        'VrDemosaic': {
            'excel_file': '/content/drive/MyDrive/VrDemosaic/Link/VrDemosaic.xlsx',
            'download_dir': '/content/drive/MyDrive/VrDemosaic/Download/',
            'save_dir': '/content/drive/MyDrive/VrDemosaic/Video/',
            'torrent_dir': '/content/drive/MyDrive/VrDemosaic/Link/Torrent/UnDownloaded',
            'torrent_downloaded_dir': '/content/drive/MyDrive/VrDemosaic/Link/Torrent/Downloaded'
        },
        'VrUncensored': {
            'excel_file': '/content/drive/MyDrive/VrUncensored/Link/VrUncensored.xlsx',
            'download_dir': '/content/drive/MyDrive/VrUncensored/Download/',
            'save_dir': '/content/drive/MyDrive/VrUncensored/Video/',
            'torrent_dir': '/content/drive/MyDrive/VrUncensored/Link/Torrent/UnDownloaded',
            'torrent_downloaded_dir': '/content/drive/MyDrive/VrUncensored/Link/Torrent/Downloaded'
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
