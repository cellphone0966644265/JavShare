# /core/file_utils.py
import os
from . import excel_handler 

def find_files_to_upload(source_dir, excel_file, sheet, table, host):
    """
    So sánh file trong thư mục với Excel để tìm các file cần upload cho một host.
    """
    try:
        # Lấy danh sách tên file (không có phần mở rộng) đã được upload cho host này
        all_uploaded_records = excel_handler.read_table(excel_file, sheet, table)
        uploaded_for_host = {
            str(record['Name']).rsplit('.', 1)[0]
            for record in all_uploaded_records
            if record.get('Host') == host
        }
        
        files_to_upload = []
        if not os.path.isdir(source_dir):
            return []
            
        for file in os.listdir(source_dir):
            full_path = os.path.join(source_dir, file)
            if not os.path.isfile(full_path):
                continue
            file_name_no_ext = os.path.basename(file).rsplit('.', 1)[0]
            if file_name_no_ext not in uploaded_for_host:
                files_to_upload.append(full_path)
                
        return files_to_upload
    except Exception as e:
        print(f"Lỗi khi tìm file cần upload: {e}")
        return []
