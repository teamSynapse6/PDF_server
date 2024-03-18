from flask import Flask, send_from_directory, abort, request, Response
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# 애플리케이션의 루트 디렉토리 기반으로 절대 경로 생성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/announcement')
def get_announcement():
    # 쿼리 파라미터에서 file_id 추출
    file_id = request.args.get('id')
    if not file_id:
        # file_id가 없으면 400 Bad Request 오류 반환
        abort(400)

    # 파일명을 안전하게 만들어 기본 파일 경로를 생성
    filename = secure_filename(file_id)
    base_filepath = os.path.join(BASE_DIR, 'file', filename)

    # 가능한 확장자 목록
    extensions = ['pdf', 'txt']

    # 확장자를 순회하며 파일 존재 여부 확인
    for ext in extensions:
        filepath = f"{base_filepath}.{ext}"
        if os.path.exists(filepath):
            # 파일이 존재하면 해당 파일 제공
            response = send_from_directory(os.path.join(BASE_DIR, 'file'), f"{filename}.{ext}")
            if ext == 'pdf':
                response.headers['Content-Type'] = 'application/pdf'
            elif ext == 'txt':
                response.headers['Content-Type'] = 'text/plain'
            return response

    # 파일이 없으면 404 오류 반환
    abort(404)

if __name__ == '__main__':
    app.run(debug=True)
