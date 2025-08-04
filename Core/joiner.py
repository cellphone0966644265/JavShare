# /core/joiner.py

import os
import argparse
import json
import subprocess
import tempfile

def main():
    """
    Module này nhận một danh sách các file video và một tên file output,
    sau đó nối chúng lại thành một file duy nhất bằng ffmpeg concat demuxer.
    """
    parser = argparse.ArgumentParser(description="Nối các file video bằng ffmpeg -c copy.")
    parser.add_argument("--files-json", required=True, help="Chuỗi JSON chứa danh sách đường dẫn các file video cần nối, theo đúng thứ tự.")
    parser.add_argument("--output-file", required=True, help="Đường dẫn file video sau khi nối.")
    parser.add_argument("--delete-parts", action='store_true', help="Thêm cờ này nếu muốn xóa các file thành phần sau khi nối thành công.")

    args = parser.parse_args()
    
    temp_list_file = None
    try:
        # 1. Tải danh sách file từ chuỗi JSON
        files_to_join = json.loads(args.files_json)

        if not files_to_join or len(files_to_join) < 2:
            raise ValueError("Cần ít nhất 2 file để thực hiện việc nối.")

        # Kiểm tra tất cả các file thành phần có tồn tại không
        for f in files_to_join:
            if not os.path.exists(f):
                raise FileNotFoundError(f"File thành phần không tồn tại: {f}")

        # 2. Tạo một file text tạm thời để chứa danh sách file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp:
            temp_list_file = tmp.name
            for file_path in files_to_join:
                # Ghi vào file theo định dạng mà ffmpeg yêu cầu
                tmp.write(f"file '{os.path.abspath(file_path)}'\n")
        
        print(f"Đã tạo file danh sách tạm thời tại: {temp_list_file}")

        # 3. Xây dựng và thực thi lệnh ffmpeg
        command = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_list_file,
            '-c', 'copy',
            '-y',
            args.output_file
        ]

        print(f"Đang thực thi lệnh: {' '.join(command)}")
        subprocess.run(command, check=True, capture_output=True)

        if not os.path.exists(args.output_file):
            raise RuntimeError("Nối file thất bại, không tìm thấy file output.")

        print(f"Nối file thành công! File output tại: {args.output_file}")
        
        # 4. Xóa các file thành phần nếu người dùng yêu cầu
        if args.delete_parts:
            print("Đang xóa các file thành phần...")
            for file_path in files_to_join:
                try:
                    os.remove(file_path)
                    print(f" -> Đã xóa: {file_path}")
                except OSError as e:
                    print(f" -> Lỗi khi xóa {file_path}: {e}")
        
        result = {"status": "success", "output_path": args.output_file}
        print(json.dumps(result))

    except Exception as e:
        error_message = {"status": "error", "message": str(e)}
        print(json.dumps(error_message, indent=4))
        exit(1)
        
    finally:
        # 5. Dọn dẹp file text tạm thời dù có lỗi hay không
        if temp_list_file and os.path.exists(temp_list_file):
            os.remove(temp_list_file)
            print(f"Đã dọn dẹp file tạm thời: {temp_list_file}")

if __name__ == '__main__':
    main()
