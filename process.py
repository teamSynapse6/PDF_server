from krwordrank.word import KRWordRank
import pandas as pd
import os

# KRWordRank를 활용한 키워드 추출을 위한 설정
min_count = 1
max_length = 10
beta = 0.85    
max_iter = 20

wordrank_extractor = KRWordRank(min_count=min_count, max_length=max_length)

# 파일에서 텍스트 읽기
def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text

# 키워드 추출 함수
def extract_keywords(texts, beta=0.85, max_iter=20):
    keywords, rank, graph = wordrank_extractor.extract(texts, beta, max_iter)
    return keywords

# 키워드 빈도수 계산 함수
def calculate_frequencies(text, keywords):
    frequencies = {}
    for keyword in keywords.keys():
        # 키워드가 문자로만 구성되어 있는지 확인합니다.
        if keyword.isalpha():  # 숫자나 기호를 포함하지 않는 경우에만 True
            # 대소문자를 구분하지 않고 키워드의 빈도수를 계산합니다.
            count = text.lower().count(keyword.lower())
            frequencies[keyword] = count
    return frequencies

# 결과를 엑셀 파일로 저장하는 함수
def save_to_excel(frequencies, output_file_name):
    # 키워드와 빈도수를 데이터프레임으로 변환
    df = pd.DataFrame(list(frequencies.items()), columns=['Keyword', 'Frequency'])
    
    # 빈도수 내림차순으로 정렬
    df = df.sort_values(by='Frequency', ascending=False)
    
    try:
        # 엑셀 파일로 저장
        df.to_excel(output_file_name, index=False)
    except Exception as e:
        print(f"엑셀 파일 저장 중 오류가 발생했습니다: {e}")

# 메인 실행 로직
if __name__ == "__main__":
    file_path = 'preinter.txt'  # 분석할 파일 경로 <<--------------여기에 txt파일 명을 넣으시면 됩니다.
    output_file_name = 'keywords.xlsx'  # 저장할 엑셀 파일 이름
    
    if os.path.exists(file_path):
        text = read_text_file(file_path)
        texts = text.split('\n')  # 문장 분리
        keywords = extract_keywords(texts)
        frequencies = calculate_frequencies(text, keywords)
        save_to_excel(frequencies, output_file_name)
        print(f"{output_file_name}에 키워드 저장 완료.")
    else:
        print(f"{file_path} 파일을 찾을 수 없습니다.")
