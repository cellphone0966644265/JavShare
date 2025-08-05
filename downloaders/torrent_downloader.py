# /downloaders/torrent_downloader.py
import libtorrent as lt
import time
import sys
import argparse
import json
import os

def main():
    parser = argparse.ArgumentParser(description="Tải file từ file .torrent.")
    parser.add_argument("-t", "--torrent-file", required=True, help="Đường dẫn đến file .torrent.")
    parser.add_argument("-o", "--output-dir", required=True, help="Thư mục lưu file đã tải.")
    args = parser.parse_args()

    try:
        ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})
        info = lt.torrent_info(args.torrent_file)
        handle = ses.add_torrent({'ti': info, 'save_path': args.output_dir})

        print(f"Bắt đầu tải: {handle.name()}")
        while not handle.status().is_seeding:
            s = handle.status()
            state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
            progress = s.progress * 100
            down_speed = s.download_rate / 1000
            up_speed = s.upload_rate / 1000
            sys.stdout.write(f"\r%.2f%% (down: %.1f kB/s up: %.1f kB/s peers: %d) %s" % (progress, down_speed, up_speed, s.num_peers, state_str[s.state]))
            sys.stdout.flush()
            time.sleep(1)
        
        print(f"\nHoàn thành tải: {handle.name()}")
        
        # Lấy danh sách các file đã được tải
        torrent_info = handle.get_torrent_info()
        downloaded_files = [os.path.join(args.output_dir, f.path) for f in torrent_info.files()]
        
        result = {"status": "success", "save_path": args.output_dir, "files": downloaded_files}
        print(json.dumps(result, indent=4, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=4, ensure_ascii=False))
        exit(1)

if __name__ == '__main__':
    main()
