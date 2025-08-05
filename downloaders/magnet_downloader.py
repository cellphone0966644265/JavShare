# /downloaders/magnet_downloader.py
import libtorrent as lt
import time
import sys
import argparse
import json
import os

def main():
    parser = argparse.ArgumentParser(description="Tải file từ link magnet.")
    parser.add_argument("-m", "--magnet-uri", required=True, help="Đường dẫn magnet (đặt trong \"\").")
    parser.add_argument("-o", "--output-dir", required=True, help="Thư mục lưu file đã tải.")
    args = parser.parse_args()

    try:
        ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})
        params = lt.parse_magnet_uri(args.magnet_uri)
        params.save_path = args.output_dir
        handle = ses.add_torrent(params)

        print("Đang lấy metadata từ magnet...")
        while not handle.status().has_metadata:
            time.sleep(1)
        
        print(f"\nBắt đầu tải: {handle.name()}")
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

        torrent_info = handle.get_torrent_info()
        downloaded_files = [os.path.join(args.output_dir, f.path) for f in torrent_info.files()]
        
        result = {"status": "success", "save_path": args.output_dir, "files": downloaded_files}
        print(json.dumps(result, indent=4, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=4, ensure_ascii=False))
        exit(1)

if __name__ == '__main__':
    main()
