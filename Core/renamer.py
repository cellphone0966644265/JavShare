# /core/renamer.py
import os
import argparse
import json

def main():
    """Đổi tên một hoặc nhiều file theo một tên gốc (base_name) cho trước."""
    parser = argparse.ArgumentParser(description="Đổi tên các file theo quy tắc.")
    parser.add_argument("--files-json", required=True, help="Chuỗi JSON chứa danh sách đường dẫn file cần đổi tên.")
    parser.add_argument("--base-name", required=True, help="Tên cơ bản để đặt cho file (không cần phần mở rộng).")
    args = parser.parse_args()

    try:
        # Tự động loại bỏ phần mở rộng từ base_name nếu có
        base_name_no_ext, _ = os.path.splitext(args.base_name)
        
        # Tải danh sách đường dẫn file từ chuỗi JSON
        files_to_rename = json.loads(args.files_json)
        
        # Sắp xếp để đảm bảo thứ tự đổi tên nhất quán (A, B, C...)
        sorted_files = sorted(list(files_to_rename))
        renamed_paths = []
        
        if len(sorted_files) == 1:
            file_path = sorted_files[0]
            dir_name = os.path.dirname(file_path)
            _, file_ext = os.path.splitext(file_path)
            new_name = base_name_no_ext + file_ext
            new_path = os.path.join(dir_name, new_name)
            os.rename(file_path, new_path)
            renamed_paths.append(new_path)
        else:
            for i, file_path in enumerate(sorted_files):
                dir_name = os.path.dirname(file_path)
                _, file_ext = os.path.splitext(file_path)
                # Thêm hậu tố _A, _B, _C...
                suffix = f'_{chr(65 + i)}'
                new_name = base_name_no_ext + suffix + file_ext
                new_path = os.path.join(dir_name, new_name)
                os.rename(file_path, new_path)
                renamed_paths.append(new_path)

        # Trả về danh sách các đường dẫn MỚI dưới dạng JSON
        print(json.dumps(renamed_paths, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=4, ensure_ascii=False))
        exit(1)

if __name__ == '__main__':
    main()
