# /core/renamer.py

import os
import argparse
import json

def main():
    """
    Module này nhận một danh sách các file mới và một tên cơ bản,
    sau đó đổi tên các file đó theo quy tắc từ file Colab gốc.
    Module này sẽ tự động loại bỏ phần mở rộng của tên cơ bản nếu có.
    """
    parser = argparse.ArgumentParser(description="Đổi tên các file mới được tải về theo quy tắc đã định.")
    parser.add_argument("--files-json", required=True, help="Chuỗi JSON chứa danh sách đường dẫn các file mới cần đổi tên.")
    parser.add_argument("--base-name", required=True, help="Tên cơ bản để đặt cho file (có thể có hoặc không có phần mở rộng).")
    
    args = parser.parse_args()

    try:
        # ---- THAY ĐỔI DUY NHẤT NẰM Ở ĐÂY ----
        # Tự động loại bỏ phần mở rộng từ base_name đầu vào, nếu có.
        # Ví dụ: nếu nhận vào "Video-A.mp4", nó sẽ trở thành "Video-A".
        #        nếu nhận vào "Video-A", nó vẫn là "Video-A".
        base_name_no_ext, _ = os.path.splitext(args.base_name)
        # ------------------------------------

        # Tải danh sách các đường dẫn file từ chuỗi JSON được truyền vào
        new_files = json.loads(args.files_json)
        
        # Sắp xếp lại danh sách để đảm bảo thứ tự đổi tên luôn nhất quán (A, B, C...)
        sorted_new_files = sorted(list(new_files))

        # Chuẩn bị một danh sách để chứa các đường dẫn sau khi đã được đổi tên
        renamed_files_paths = []
        
        # TRƯỜNG HỢP 1: Nếu chỉ có một file duy nhất được tải về
        if len(sorted_new_files) == 1:
            file_path = sorted_new_files[0]
            _, file_ext = os.path.splitext(file_path)
            
            # Sử dụng base_name_no_ext đã được xử lý
            new_name = base_name_no_ext + file_ext
            new_path = os.path.join(os.path.dirname(file_path), new_name)
            
            print(f"Đổi tên file đơn: '{os.path.basename(file_path)}' -> '{new_name}'")
            os.rename(file_path, new_path)
            renamed_files_paths.append(new_path)
        
        # TRƯỜNG HỢP 2: Nếu có nhiều file được tải về
        else:
            for i, file_path in enumerate(sorted_new_files):
                _, file_ext = os.path.splitext(file_path)
                suffix = f'_{chr(65 + i)}'
                
                # Sử dụng base_name_no_ext đã được xử lý
                new_name = base_name_no_ext + suffix + file_ext
                new_path = os.path.join(os.path.dirname(file_path), new_name)
                
                print(f"Đổi tên file trong nhóm: '{os.path.basename(file_path)}' -> '{new_name}'")
                os.rename(file_path, new_path)
                renamed_files_paths.append(new_path)

        # Trả về danh sách các đường dẫn MỚI dưới dạng JSON
        print(json.dumps(renamed_files_paths, ensure_ascii=False))

    except Exception as e:
        error_message = {"status": "error", "message": str(e)}
        print(json.dumps(error_message, indent=4, ensure_ascii=False))
        exit(1)

if __name__ == '__main__':
    main()
