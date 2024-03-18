from flask import Flask, send_from_directory, abort, Response
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# 애플리케이션의 루트 디렉토리 기반으로 절대 경로 생성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/announcement/<file_id>')
def get_announcement(file_id):
    try:
        # 파일명을 안전하게 만들어 파일 경로를 결합
        filename = secure_filename(f"{file_id}.pdf")
        filepath = os.path.join(BASE_DIR, 'file', filename)
        
        # 파일이 실제로 존재하는지 확인
        if not os.path.exists(filepath):
            # 파일이 없으면 404 오류 반환
            abort(404)
        
        # send_from_directory를 사용하여 파일 제공, 브라우저에서 직접 열 수 있도록 설정
        response = send_from_directory(os.path.join(BASE_DIR, 'file'), filename)
        # PDF 파일을 웹 브라우저에서 직접 열기 위해 Content-Type 설정
        response.headers['Content-Type'] = 'application/pdf'
        return response
    except FileNotFoundError:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True)
