# /core/joiner.py
import os
import argparse
import json
import subprocess
import tempfile

def main():
    """Nối các file video thành một file duy nhất bằng ffmpeg."""
    parser = argparse.ArgumentParser(description="Nối các file video bằng ffmpeg concat demuxer.")
    parser.add_argument("--files-json", required=True, help="Chuỗi JSON chứa danh sách file cần nối, theo đúng thứ tự.")
    parser.add_argument("--output-file", required=True, help="Đường dẫn file output sau khi nối.")
    parser.add_argument("--delete-parts", action='store_true', help="Xóa các file thành phần sau khi nối thành công.")
    args = parser.parse_args()
    
    temp_list_file = None
    try:
        files_to_join = json.loads(args.files_json)
        if not files_to_join or len(files_to_join) < 2:
            raise ValueError("Cần ít nhất 2 file để thực hiện việc nối.")

        # Tạo file text tạm thời chứa danh sách file cho ffmpeg
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp:
            temp_list_file = tmp.name
            for file_path in files_to_join:
                if not os.path.exists(file_path): raise FileNotFoundError(f"File không tồn tại: {file_path}")
                tmp.write(f"file '{os.path.abspath(file_path)}'\n")
        
        # Lệnh ffmpeg để nối file mà không cần re-encode
        command = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', temp_list_file,
            '-c', 'copy', '-y', args.output_file
        ]
        subprocess.run(command, check=True, capture_output=True)

        if not os.path.exists(args.output_file):
            raise RuntimeError("Nối file thất bại, không tìm thấy file output.")

        if args.delete_parts:
            for file_path in files_to_join:
                try: os.remove(file_path)
                except OSError as e: print(f"Lỗi khi xóa {file_path}: {e}")
        
        print(json.dumps({"status": "success", "output_path": args.output_file}))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=4))
        exit(1)
    finally:
        # Luôn dọn dẹp file tạm
        if temp_list_file and os.path.exists(temp_list_file):
            os.remove(temp_list_file)

if __name__ == '__main__':
    main()
