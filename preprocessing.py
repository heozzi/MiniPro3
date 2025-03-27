import pandas as pd
import re 



with open("Data/cover_letters.csv", "r",encoding='utf-8') as f:
	data = f.read()


data = re.sub(r"\\","",data)

idx = 12442
company = ""
position = ""
Q = ""
A = ""

newdata = data.split('\n')

result = []
while newdata : 
    tmp_text = newdata.pop(0)
    if not tmp_text : continue
    if tmp_text == '"' : continue
    if tmp_text == ' ' : continue

    print(tmp_text,len(tmp_text.split(',')))
    check_1 = [True for _ in tmp_text[1:6] if not (0<=ord(_)-48<=9)]
    if company == 'Error' :
        if not tmp_text.count('1.') : 
            continue
    try : 
        if not check_1 : # 아무것도 없을때
            if (result and len(result[-1]) == 3) : 
                result[-1].append(A)
            tmpidx = tmp_text.index('1.')
            tmp_text = tmp_text[:tmpidx] + re.sub(','," ",tmp_text[tmpidx:])
            tmp_text = re.sub(r'"',"",tmp_text)
            
            _,company,position,Q =  tmp_text.split(',')
            Q = Q[3:]
            result.append([company,position,Q])
            A = ""
        elif(0<=ord(tmp_text[0])-48<=9) :
            result[-1].append(A)
            Q = tmp_text[3:]
            result.append([company,position,Q])
            A = ""
        else : 
            A+=tmp_text
    except : 
        company = 'Error'
        

print(result)