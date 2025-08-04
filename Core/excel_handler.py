# /core/excel_handler.py

import pandas as pd
import openpyxl
import argparse
import json
import tempfile
import shutil
import os
from threading import Lock

lock = Lock()

def read_table(ws, table_name):
    """Hàm phụ để đọc dữ liệu từ một bảng và trả về list của dictionary."""
    table = ws.tables[table_name]
    data_range = ws[table.ref]
    
    rows = list(data_range)
    columns = [cell.value for cell in rows[0]]
    data = [[cell.value for cell in row] for row in rows[1:]]
    
    df = pd.DataFrame(data, columns=columns)
    return df.to_dict(orient='records')

def update_cell(wb, ws, table_name, row_index, column, value):
    """Hàm phụ để cập nhật một ô trong bảng."""
    table = ws.tables[table_name]
    header_range = ws[table.ref.split(':')[0]]
    columns = [cell.value for cell in header_range[0]]
    
    if column not in columns:
        raise ValueError(f"Không tìm thấy cột '{column}' trong bảng '{table_name}'.")

    col_index = columns.index(column) + table.ref_range.min_col
    actual_row = int(row_index) + table.ref_range.min_row + 1
    
    ws.cell(row=actual_row, column=col_index, value=value)
    return f"Đã cập nhật dòng {row_index}, cột '{column}' thành công."

def write_row(ws, table_name, data_json):
    """Hàm phụ để ghi một dòng mới vào cuối bảng."""
    table = ws.tables[table_name]
    header_range = ws[table.ref.split(':')[0]]
    columns = [cell.value for cell in header_range[0]]
    
    new_data = json.loads(data_json)
    next_row = table.ref_range.max_row + 1

    for col_name, value in new_data.items():
        if col_name in columns:
            col_idx = columns.index(col_name) + table.ref_range.min_col
            ws.cell(row=next_row, column=col_idx, value=value)

    table.ref = f"{table.ref.split(':')[0]}:{table.ref_range.max_col_letter}{next_row}"
    return f"Đã ghi dòng mới vào bảng '{table_name}' thành công."

def main():
    """Hàm chính điều phối các hoạt động từ dòng lệnh."""
    parser = argparse.ArgumentParser(description="Tương tác với file Excel qua dòng lệnh, trả về kết quả JSON.")
    parser.add_argument("-f", "--file", required=True, help="Đường dẫn đến file Excel.")
    parser.add_argument("-s", "--sheet", required=True, help="Tên sheet.")
    parser.add_argument("-t", "--table", required=True, help="Tên bảng (table).")
    parser.add_argument("-a", "--action", required=True, choices=['read', 'update', 'write'], help="Hành động: read, update, write.")
    parser.add_argument("--row-index", help="(update) Chỉ số dòng cần update (bắt đầu từ 0).")
    parser.add_argument("--column", help="(update) Tên cột cần update.")
    parser.add_argument("--value", help="(update) Giá trị mới để update.")
    parser.add_argument("--data-json", help="(write) Dữ liệu JSON cho dòng mới. Ví dụ: '{\"Name\":\"FileA\", \"Url\":\"http://a.com\"}'")
    
    args = parser.parse_args()
    
    try:
        if not os.path.exists(args.file):
            raise FileNotFoundError(f"File không tồn tại: {args.file}")
        
        with lock:
            wb = openpyxl.load_workbook(args.file)
            if args.sheet not in wb.sheetnames:
                raise ValueError(f"Không tìm thấy sheet '{args.sheet}'")
            ws = wb[args.sheet]
            if args.table not in ws.tables:
                raise ValueError(f"Không tìm thấy bảng '{args.table}'")

            result = {}
            if args.action == 'read':
                result = read_table(ws, args.table)
            elif args.action == 'update':
                message = update_cell(wb, ws, args.table, args.row_index, args.column, args.value)
                result = {"status": "success", "message": message}
            elif args.action == 'write':
                message = write_row(ws, args.table, args.data_json)
                result = {"status": "success", "message": message}
            
            if args.action in ['update', 'write']:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', mode='wb') as tmp:
                    wb.save(tmp.name)
                shutil.move(tmp.name, args.file)
            
            print(json.dumps(result, indent=4, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=4, ensure_ascii=False))
        exit(1)

if __name__ == '__main__':
    main()
