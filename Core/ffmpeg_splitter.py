# /core/ffmpeg_splitter.py
import os
import argparse
import json
import subprocess
import math

def get_video_duration(file_path):
    """Sử dụng ffprobe để lấy thời lượng video (giây)."""
    command = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', file_path
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        return None

def main():
    parser = argparse.ArgumentParser(description="Chia video theo dung lượng tối đa hoặc các mốc thời gian.")
    # Thêm 2 lựa chọn, nhưng logic sẽ chỉ cho phép một trong hai chạy
    parser.add_argument("--file-path", required=True, help="Đường dẫn file video cần xử lý.")
    parser.add_argument("--max-size-gb", type=int, help="CHẾ ĐỘ TỰ ĐỘNG: Dung lượng tối đa (GB) cho mỗi phần.")
    parser.add_argument("--start-times", nargs='+', type=float, help="CHẾ ĐỘ THỦ CÔNG: Danh sách các mốc thời gian bắt đầu (giây) để chia.")
    
    args = parser.parse_args()
    
    try:
        if not os.path.exists(args.file_path):
            raise FileNotFoundError(f"File không tồn tại: {args.file_path}")

        base_name, extension = os.path.splitext(args.file_path)
        part_paths = []
        status = ""

        # --- CHẾ ĐỘ 1: CHIA THỦ CÔNG THEO MỐC THỜI GIAN ---
        if args.start_times:
            print(f"Phát hiện chế độ chia thủ công theo các mốc thời gian: {args.start_times}")
            duration = get_video_duration(args.file_path)
            if duration is None:
                raise RuntimeError("Không thể lấy thời lượng video để chia thủ công.")
            
            # Sắp xếp các mốc thời gian và thêm tổng thời lượng vào cuối để biết điểm kết thúc
            split_points = sorted(args.start_times) + [duration]
            
            for i in range(len(split_points) - 1):
                start = split_points[i]
                end = split_points[i+1]
                
                if start >= end: continue

                part_path = f"{base_name}_part{i + 1}{extension}"
                part_paths.append(part_path)
                
                # Dùng -to để cắt chính xác hơn giữa hai mốc thời gian
                command = [
                    'ffmpeg', '-i', args.file_path,
                    '-ss', str(start), '-to', str(end),
                    '-c', 'copy', '-y', part_path
                ]
                print(f"Đang tạo phần {i + 1} (từ {start:.2f}s đến {end:.2f}s)...")
                subprocess.run(command, check=True, capture_output=True, text=True)

            status = "manual_split"

        # --- CHẾ ĐỘ 2: CHIA TỰ ĐỘNG THEO DUNG LƯỢNG ---
        elif args.max_size_gb:
            file_size_bytes = os.path.getsize(args.file_path)
            max_size_bytes = args.max_size_gb * 1024 * 1024 * 1024

            if file_size_bytes <= max_size_bytes:
                print(json.dumps({"status": "unsplit", "files": [args.file_path]}))
                return

            print(f"File lớn hơn {args.max_size_gb}GB. Bắt đầu chia tự động...")
            duration = get_video_duration(args.file_path)
            if duration is None:
                raise RuntimeError("Không thể lấy thời lượng video để chia tự động.")
            
            num_parts = math.ceil(file_size_bytes / max_size_bytes)
            duration_per_part = duration / num_parts
            
            for i in range(num_parts):
                part_path = f"{base_name}_part{i + 1}{extension}"
                part_paths.append(part_path)
                start_time = i * duration_per_part
                
                command = [
                    'ffmpeg', '-ss', str(start_time), '-i', args.file_path,
                    '-t', str(duration_per_part), '-c', 'copy', '-y', part_path
                ]
                subprocess.run(command, check=True, capture_output=True, text=True)
            
            status = "auto_split"
        
        else:
            raise ValueError("Phải cung cấp --max-size-gb hoặc --start-times.")

        # Sau khi chia xong (ở cả 2 chế độ), xóa file gốc
        os.remove(args.file_path)

        result = {"status": status, "files": part_paths}
        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=4))
        exit(1)

if __name__ == '__main__':
    main()
