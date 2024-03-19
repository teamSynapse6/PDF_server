from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import requests
import fitz  # PyMuPDF
import os

app = Flask(__name__)

# 애플리케이션의 루트 디렉토리 기반으로 절대 경로 생성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.join(BASE_DIR, 'file')
PROCESSED_FILE_DIR = os.path.join(BASE_DIR, 'processed_file')

# processed_file 디렉토리가 없으면 생성
if not os.path.exists(PROCESSED_FILE_DIR):
    os.makedirs(PROCESSED_FILE_DIR)


@app.route('/announcement/upload', methods=['POST'])
def upload_files():
    data = request.json
    for item in data:
        file_url = item['url']
        file_id = item['id']
        temp_path = os.path.join(BASE_DIR, f"{file_id}.temp") # 임시 확장자로 저장
        
        # 파일 다운로드
        response = requests.get(file_url)
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        
        try:
            # 다운로드한 파일이 PDF인지 확인
            doc = fitz.open(temp_path)
            # PDF를 TXT로 변환
            text = ''
            for page in doc:
                text += page.get_text()
            
            txt_path = os.path.join(PROCESSED_FILE_DIR, f"{file_id}.txt")
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(text)

            doc.close() # PDF 파일 사용 후 닫기
        except Exception as e:
            print(f"File {file_id} is not a PDF or could not be processed. Error: {e}")
            os.remove(temp_path) # PDF가 아니면 임시 파일 삭제
            continue # 다음 아이템으로 넘어가기
        
        # 처리 완료 후 임시 파일 삭제
        os.remove(temp_path)

    return jsonify({"message": "Files processed successfully."}), 20



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
