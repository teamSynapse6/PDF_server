import olefile
import os
import zlib
import struct

# 스크립트 파일의 위치를 기반으로 한 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.join(BASE_DIR, 'hwp_file')  # HWP 파일이 위치한 폴더
HWP_FILENAME = 'file.hwp'  # HWP 파일 이름
PROCESSED_FILE_DIR = os.path.join(BASE_DIR, 'processed_file')  # TXT 파일을 저장할 폴더

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

def convert_hwp_to_txt(hwp_relative_path, output_folder):
    # HWP 파일의 전체 경로
    hwp_path = os.path.join(FILE_DIR, hwp_relative_path)

    # 출력 폴더가 존재하지 않으면 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # HWP 파일에서 텍스트 추출
    try:
        extracted_text = get_hwp_text(hwp_path)

        # 파일 이름 설정 (확장자 변경)
        output_file_name = hwp_relative_path.replace('.hwp', '.txt')
        output_file_path = os.path.join(output_folder, output_file_name)

        # 추출된 텍스트를 TXT 파일로 저장
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(extracted_text)

        print(f"파일이 저장되었습니다: {output_file_path}")
    except Exception as e:
        print(f"파일 처리 중 오류가 발생했습니다: {e}")

# 함수 호출
convert_hwp_to_txt(HWP_FILENAME, PROCESSED_FILE_DIR)
