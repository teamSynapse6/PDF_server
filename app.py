from flask import Flask, request, jsonify, abort, Response
import requests
import fitz 
import os
from werkzeug.utils import secure_filename
import shutil
import olefile
import os
import zlib
import struct


app = Flask(__name__)

# 애플리케이션의 루트 디렉토리 기반으로 절대 경로 생성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.join(BASE_DIR, 'file')
PROCESSED_FILE_DIR = os.path.join(BASE_DIR, 'processed_file')
PRE_FILE_DIR = os.path.join(BASE_DIR, 'pre_file')



#로컬 파일을 txt로 변환
@app.route('/get_transform_from_prefile', methods=['GET'])
def get_transform_from_prefile():
    # pre_file 디렉토리에서 hwp와 pdf 파일 목록을 가져옵니다.
    files = [f for f in os.listdir(PRE_FILE_DIR) if os.path.isfile(os.path.join(PRE_FILE_DIR, f)) and f.split('.')[-1] in ['hwp', 'pdf']]
    
    # 임시로 파일 URL 대신 파일 경로를 사용하는 데이터 구조를 생성합니다.
    items_to_process = [{
        "path": os.path.join(PRE_FILE_DIR, file),
        "id": os.path.splitext(file)[0],  # 파일 이름에서 확장자를 제거하여 id를 생성합니다.
        "format": file.split('.')[-1]  # 확장자를 format으로 사용합니다.
    } for file in files]
    
    # 각 파일을 처리합니다.
    for item in items_to_process:
        file_path = item["path"]
        file_id = item["id"]
        file_format = item["format"]
        
        # 파일 형식에 따른 처리를 수행합니다.
        try:
            if file_format == 'pdf':
                convert_pdf_to_txt(file_path, file_id)
            elif file_format == 'hwp':
                convert_hwp_to_txt(file_path, PROCESSED_FILE_DIR)
            # 성공한 항목을 로그로 기록할 수 있습니다.
            print(f"Processed: {file_id}.{file_format}")
        except Exception as e:
            # 실패한 항목을 처리합니다.
            print(f"Failed to process {file_id}.{file_format}: {e}")
    
    return jsonify({"status": "finished", "message": "Files processed"}), 200



# 저장된 파일 리스트 get 메소드
@app.route('/validation', methods=['GET'])
def validate_files():
    # PROCESSED_FILE_DIR 디렉토리에 있는 모든 파일의 이름을 리스트로 가져옵니다.
    filenames = os.listdir(PROCESSED_FILE_DIR)
    
    # 파일명에서 '.txt' 확장자를 제거하여 id 리스트를 생성합니다.
    file_ids = [filename[:-4] for filename in filenames if filename.endswith('.txt')]
    
    # id 리스트를 JSON 형태로 반환합니다.
    return jsonify({"file_ids": file_ids}), 200

# 저장된 특정 공고 정보 가져오기
@app.route('/announcement')
def get_announcement():
    file_id = request.args.get('id')
    if not file_id:
        abort(400)  # file_id가 없으면 400 Bad Request 오류 반환

    filename = secure_filename(file_id) + '.txt'
    filepath = os.path.join(PROCESSED_FILE_DIR, filename)

    if os.path.exists(filepath):
        # 파일이 존재하면 해당 파일의 내용을 읽어서 반환
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        return Response(content, mimetype='text/plain; charset=utf-8')
    else:
        abort(404)  # 파일이 없으면 404 오류 반환

# 아이템 삭제 메소드
@app.route('/announcement/delete', methods=['DELETE'])
def delete_files():
    data = request.get_json()
    file_ids = data.get('id')
    if not file_ids:
        return jsonify({"error": "No file ids provided"}), 400

    for file_id in file_ids:
        filename = f"{file_id}.txt"
        filepath = os.path.join(PROCESSED_FILE_DIR, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error deleting file {file_id}: {e}")
    return jsonify({"status": "finished"}), 200


# processed_file 디렉토리가 없으면 생성
if not os.path.exists(PROCESSED_FILE_DIR):
    os.makedirs(PROCESSED_FILE_DIR)

# pdf, hwp id 반환후 다운 처리 프로세스
@app.route('/announcement/upload', methods=['POST'])
def upload_files():
    data = request.json
    success_items = []
    failed_items = []

    for item in data:
        file_url = item['url']
        file_id = item['id']
        file_format = item['format']
        temp_path = os.path.join(BASE_DIR, f"{file_id}.{file_format}")  # 원본 파일 확장자로 저장

        # 지원되는 파일 형식만 처리
        if file_format in ['hwp', 'pdf', 'txt']:
            try:
                # 파일 다운로드
                response = requests.get(file_url, stream=True)
                with open(temp_path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)

                print(f"Downloaded file saved as: {temp_path}")

                # 파일 형식에 따른 처리
                if file_format == 'pdf':
                    # PDF 파일을 TXT로 변환
                    convert_pdf_to_txt(temp_path, file_id)
                elif file_format == 'hwp':
                    # HWP 파일을 TXT로 변환
                    convert_hwp_to_txt(temp_path, PROCESSED_FILE_DIR)
                elif file_format == 'txt':
                    # TXT 파일은 바로 저장
                    shutil.move(temp_path, os.path.join(PROCESSED_FILE_DIR, f"{file_id}.txt"))

                success_items.append(file_id)

            except Exception as e:
                print(f"Error processing file {file_id}: {e}")
                failed_items.append(file_id)
                if os.path.exists(temp_path):
                    os.remove(temp_path)  # 실패 시 임시 파일 삭제
        else:
            print(f"Unsupported file format for file {file_id}")
            failed_items.append(file_id)

    return jsonify({"status": "finished", "success_items": success_items, "failed_items": failed_items}), 200

def convert_pdf_to_txt(temp_path, file_id):
    try:
        # 다운로드한 PDF 파일 열기
        doc = fitz.open(temp_path)
        text = ''
        for page in doc:
            text += page.get_text()

        txt_path = os.path.join(PROCESSED_FILE_DIR, f"{file_id}.txt")
        with open(txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(text)

        doc.close()  # PDF 파일 사용 후 닫기
        os.remove(temp_path)  # 처리 완료 후 원본 PDF 파일 삭제
    except Exception as e:
        print(f"PDF to TXT conversion failed for {file_id}: {e}")
        raise e
    
def get_hwp_text(filename):
    with olefile.OleFileIO(filename) as f:
        dirs = f.listdir()

        # 문서 포맷 압축 여부 확인
        header = f.openstream("FileHeader")
        header_data = header.read()
        is_compressed = (header_data[36] & 1) == 1

        # Body Sections 불러오기
        nums = []
        for d in dirs:
            if d[0] == "BodyText":
                nums.append(int(d[1][len("Section"):]))
        sections = ["BodyText/Section"+str(x) for x in sorted(nums)]

        # 전체 text 추출
        text = ""
        for section in sections:
            bodytext = f.openstream(section)
            data = bodytext.read()
            if is_compressed:
                unpacked_data = zlib.decompress(data, -15)
            else:
                unpacked_data = data

            # 각 Section 내 text 추출    
            section_text = ""
            i = 0
            size = len(unpacked_data)
            while i < size:
                header = struct.unpack_from("<I", unpacked_data, i)[0]
                rec_type = header & 0x3ff
                rec_len = (header >> 20) & 0xfff

                if rec_type in [67]:  # 67은 텍스트 블록을 의미
                    rec_data = unpacked_data[i+4:i+4+rec_len]
                    section_text += rec_data.decode('utf-16')
                    section_text += "\n"

                i += 4 + rec_len

            text += section_text
            text += "\n"

        return text
    
def convert_hwp_to_txt(hwp_path, output_folder):
    try:
        extracted_text = get_hwp_text(hwp_path)

        file_id = os.path.basename(hwp_path).split('.')[0]
        output_file_name = f"{file_id}.txt"
        output_file_path = os.path.join(output_folder, output_file_name)

        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(extracted_text)

        print(f"파일이 저장되었습니다: {output_file_path}")
    except Exception as e:
        print(f"파일 처리 중 오류가 발생했습니다: {e}")
        raise
    finally:
        # 변환 작업이 완료된 후 원본 HWP 파일 삭제
        if os.path.exists(hwp_path):
            os.remove(hwp_path)
            print(f"원본 파일이 삭제되었습니다: {hwp_path}")

if __name__ == '__main__':
    app.run(debug=True)
