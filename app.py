from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import requests
import fitz  # PyMuPDF
import os
import subprocess  # subprocess 모듈 추가

app = Flask(__name__)

# 애플리케이션의 루트 디렉토리 기반으로 절대 경로 생성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.join(BASE_DIR, 'file')
PROCESSED_FILE_DIR = os.path.join(BASE_DIR, 'processed_file')

# processed_file 디렉토리가 없으면 생성
if not os.path.exists(PROCESSED_FILE_DIR):
    os.makedirs(PROCESSED_FILE_DIR)


# HWP 파일을 TXT 파일로 변환하는 함수
def convert_hwp_to_txt(hwp_path, txt_path):
    command = ["hwp5txt", hwp_path, "-o", txt_path]
    subprocess.run(command, check=True)


@app.route('/announcement/upload', methods=['POST'])
def upload_files():
    data = request.json
    success_ids = []  # 성공한 아이템 ID 저장
    failed_ids = []   # 실패한 아이템 ID 저장

    for item in data:
        file_url = item['url']
        file_id = item['id']
        temp_path = os.path.join(BASE_DIR, f"{file_id}.temp")
        
        try:
            # 파일 다운로드
            response = requests.get(file_url)
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            if temp_path.endswith('.pdf') or temp_path.endswith('.hwp'):
                if temp_path.endswith('.pdf'):
                    # PDF 처리 로직
                    doc = fitz.open(temp_path)
                    text = ''
                    for page in doc:
                        text += page.get_text()
                    txt_path = os.path.join(PROCESSED_FILE_DIR, f"{file_id}.txt")
                    with open(txt_path, 'w', encoding='utf-8') as txt_file:
                        txt_file.write(text)
                    doc.close()
                elif temp_path.endswith('.hwp'):
                    # HWP 처리 로직
                    txt_path = os.path.join(PROCESSED_FILE_DIR, f"{file_id}.txt")
                    convert_hwp_to_txt(temp_path, txt_path)
                
                success_ids.append(file_id)  # 성공한 경우 ID 추가
            else:
                raise ValueError("Unsupported file format")
        except Exception as e:
            print(f"Failed to process file {file_id}. Error: {e}")
            failed_ids.append(file_id)  # 실패한 경우 ID 추가
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)  # 처리 후 임시 파일 삭제

    return jsonify({"message": "Files processing completed.", "success_ids": success_ids, "failed_ids": failed_ids}), 200



@app.route('/announcement')
def get_announcement():
    # 쿼리 파라미터에서 file_id 추출
    file_id = request.args.get('id')
    if not file_id:
        # file_id가 없으면 400 Bad Request 오류 반환
        abort(400)

    # 파일명을 안전하게 만들어 기본 파일 경로를 생성
    filename = secure_filename(file_id)

    # 파일 경로 생성 (무조건 .txt 확장자를 가정)
    filepath = os.path.join(PROCESSED_FILE_DIR, f"{filename}.txt")
    if os.path.exists(filepath):
        # 파일이 존재하면 해당 파일 제공
        response = send_from_directory(PROCESSED_FILE_DIR, f"{filename}.txt")
        # 텍스트 파일의 경우 UTF-8 인코딩을 명시
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        return response
    else:
        # 파일이 없으면 404 오류 반환
        abort(404)


if __name__ == '__main__':
    app.run(debug=True)
