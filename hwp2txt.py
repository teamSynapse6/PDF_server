import os

path = "hwp_file"
exefile = 'hwp5txt'

res = []
for root, dirs, files in os.walk(path):
    rootpath = os.path.join(os.path.abspath(path), root)
    for file in files:
        filepath = os.path.join(rootpath, file)
        res.append(filepath)

for result in res:
    # .hwp 파일을 .txt로 변환
    filename = result[:-4] + ".txt"
    output = '--output ' + '"' + filename + '"'
    result = '"' + result + '"'
    command = exefile + " " + output + " " + result
    print(command)
    os.system(command)
    
    # 변환된 .txt 파일의 내용을 읽어서 출력
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
        print(content)
