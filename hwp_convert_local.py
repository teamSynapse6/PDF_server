from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import requests
import os
import olefile


app = Flask(__name__)

# 애플리케이션의 루트 디렉토리 기반으로 절대 경로 생성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.join(BASE_DIR, 'file')
PROCESSED_FILE_DIR = os.path.join(BASE_DIR, 'processed_file')

# processed_file 디렉토리가 없으면 생성
if not os.path.exists(PROCESSED_FILE_DIR):
    os.makedirs(PROCESSED_FILE_DIR)

def convert_hwp_to_txt(hwp_path, txt_path):
    try:
        with olefile.OleFileIO(hwp_path) as f:
            if f.exists('PrvText'):
                encoded_text = f.openstream('PrvText').read()
                decoded_text = encoded_text.decode('utf-16')
                with open(txt_path, 'w', encoding='utf-8') as txt_file:
                    txt_file.write(decoded_text)
            else:
                raise ValueError("PrvText stream not found in HWP file")
    except Exception as e:
        print(f"Error converting file: {e}")
        raise

def main():
    # HWP 파일 경로와 변환될 TXT 파일의 경로 지정
    hwp_path = os.path.join(BASE_DIR, "hwp_file/(공고문) 2024년_해외실증(PoC)_지원_프로그램_창업기업_모집_공고_★.hwp")  # 'example.hwp'를 실제 파일명으로 변경
    txt_path = os.path.join(PROCESSED_FILE_DIR, "converted.txt")

    convert_hwp_to_txt(hwp_path, txt_path)
    print(f"Conversion completed: {txt_path}")

if __name__ == "__main__":
    main()
