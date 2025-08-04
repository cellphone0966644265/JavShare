# /core/ffmpeg_splitter.py

import os
import argparse
import json
import subprocess
import math

def get_video_duration(file_path):
    """Sử dụng ffprobe để lấy tổng thời lượng của video (tính bằng giây)."""
    command = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', file_path
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Lỗi khi lấy thời lượng video cho file '{file_path}': {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Chia video theo dung lượng tối đa hoặc theo các mốc thời gian cho trước.")
    parser.add_argument("--file-path", required=True, help="Đường dẫn đến file video cần kiểm tra.")
    
    # Tham số cho chế độ tự động
    parser.add_argument("--max-size-gb", type=int, help="Dung lượng tối đa (GB) cho chế độ chia tự động.")
    
    # Tham số cho chế độ thủ công
    parser.add_argument("--start-times", nargs='+', type=float, help="Danh sách các thời điểm bắt đầu (bằng giây) để chia video theo cách thủ công.")
    
    args = parser.parse_args()
    
    try:
        if not os.path.exists(args.file_path):
            raise FileNotFoundError(f"File không tồn tại: {args.file_path}")

        base_name, extension = os.path.splitext(args.file_path)
        part_paths = []

        # --- KIỂM TRA XEM NGƯỜI DÙNG CÓ CUNG CẤP THỜI GIAN CỤ THỂ KHÔNG ---
        if args.start_times:
            # --- CHẾ ĐỘ 1: CHIA THEO CÁC MỐC THỜI GIAN THỦ CÔNG ---
            print(f"Phát hiện chế độ chia thủ công theo các mốc thời gian: {args.start_times}")
            
            # Sắp xếp các mốc thời gian và thêm tổng thời lượng vào cuối để biết điểm kết thúc
            start_times = sorted(args.start_times)
            duration = get_video_duration(args.file_path)
            if duration is None:
                raise RuntimeError("Không thể lấy được thời lượng video để chia thủ công.")
                
            split_points = start_times + [duration]
            
            for i in range(len(split_points) - 1):
                start = split_points[i]
                end = split_points[i+1]
                
                if start >= end: continue # Bỏ qua nếu điểm bắt đầu lớn hơn hoặc bằng điểm kết thúc

                part_path = f"{base_name}_part{i + 1}{extension}"
                part_paths.append(part_path)
                
                # Dùng -to để cắt chính xác hơn
                command = [
                    'ffmpeg',
                    '-i', args.file_path,
                    '-ss', str(start),
                    '-to', str(end),
                    '-c', 'copy',
                    '-y',
                    part_path
                ]
                print(f"Đang tạo phần {i + 1} (từ {start:.2f}s đến {end:.2f}s)...")
                subprocess.run(command, check=True, capture_output=True)

            status = "manual_split"

        else:
            # --- CHẾ ĐỘ 2: CHIA TỰ ĐỘNG THEO DUNG LƯỢNG (LOGIC CŨ) ---
            if not args.max_size_gb:
                raise ValueError("Phải cung cấp --max-size-gb nếu không dùng --start-times.")

            file_size_bytes = os.path.getsize(args.file_path)
            max_size_bytes = args.max_size_gb * 1024 * 1024 * 1024

            if file_size_bytes <= max_size_bytes:
                print(f"File '{os.path.basename(args.file_path)}' không cần chia nhỏ.")
                result = {"status": "unsplit", "files": [args.file_path]}
                print(json.dumps(result))
                return

            print(f"File '{os.path.basename(args.file_path)}' lớn hơn {args.max_size_gb}GB. Bắt đầu chia tự động...")
            duration = get_video_duration(args.file_path)
            
            num_parts = math.ceil(file_size_bytes / max_size_bytes)
            duration_per_part = duration / num_parts
            
            for i in range(num_parts):
                part_path = f"{base_name}_part{i + 1}{extension}"
                part_paths.append(part_path)
                start_time = i * duration_per_part
                
                # Dùng -t để cắt theo khoảng thời gian
                command = [
                    'ffmpeg',
                    '-ss', str(start_time),
                    '-i', args.file_path,
                    '-t', str(duration_per_part),
                    '-c', 'copy',
                    '-y',
                    part_path
                ]
                print(f"Đang tạo phần {i + 1}/{num_parts}...")
                subprocess.run(command, check=True, capture_output=True)
            
            status = "auto_split"

        # Sau khi chia xong (ở cả 2 chế độ), xóa file gốc
        os.remove(args.file_path)
        print(f"Đã xóa file gốc: {args.file_path}")

        result = {"status": status, "files": part_paths}
        print(json.dumps(result))

    except Exception as e:
        error_message = {"status": "error", "message": str(e)}
        print(json.dumps(error_message, indent=4))
        exit(1)

if __name__ == '__main__':
    main()
