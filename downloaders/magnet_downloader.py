# /downloaders/magnet_downloader.py

import libtorrent as lt
import time
import sys
import argparse
import json
import os

def main():
    """Hàm chính để tải file từ một đường dẫn magnet."""
    parser = argparse.ArgumentParser(description="Tải file từ một link magnet và trả về kết quả JSON.")
    parser.add_argument("-m", "--magnet-uri", required=True, help="Đường dẫn magnet. (Lưu ý: Đặt trong dấu \"\")")
    parser.add_argument("-o", "--output-dir", required=True, help="Thư mục để lưu file đã tải.")

    args = parser.parse_args()

    try:
        # Cấu hình và bắt đầu session torrent
        ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})
        params = lt.parse_magnet_uri(args.magnet_uri)
        params.save_path = args.output_dir
        handle = ses.add_torrent(params)

        print("Đang lấy metadata từ magnet link...")
        # Chờ đến khi metadata được tải về
        while not handle.status().has_metadata:
            sys.stdout.write(f"\rTrạng thái: {handle.status().state}")
            sys.stdout.flush()
            time.sleep(1)
        
        print(f"\nBắt đầu tải: {handle.name()}")
        # Vòng lặp hiển thị trạng thái cho đến khi tải xong
        while not handle.status().is_seeding:
            s = handle.status()
            state_str = ['queued', 'checking', 'downloading metadata', \
                    'downloading', 'finished', 'seeding', 'allocating']

            sys.stdout.write(
                f"\r%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s" %
                (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
                s.num_peers, state_str[s.state])
            )
            sys.stdout.flush()
            time.sleep(1)

        print(f"\nHoàn thành tải: {handle.name()}")

        # Lấy danh sách các file đã được tải
        torrent_info = handle.get_torrent_info()
        downloaded_files = [os.path.join(args.output_dir, f.path) for f in torrent_info.files()]

        result = {
            "status": "success",
            "save_path": args.output_dir,
            "files": downloaded_files
        }
        print(json.dumps(result, indent=4, ensure_ascii=False))

    except Exception as e:
        error_message = {"status": "error", "message": str(e)}
        print(json.dumps(error_message, indent=4, ensure_ascii=False))
        exit(1)

if __name__ == '__main__':
    main()
