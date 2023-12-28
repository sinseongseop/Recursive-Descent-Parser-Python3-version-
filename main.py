import sys

#주요 전역변수들
code_position=0 #코드에서 몇번째 글자를 가르키고 있는가?
token_count=0 # 몇개의 토큰을 가지고 있는가?
next_char=0 #다음 문자
lexeme="" # 최소 문자열 단위
token_string=[] #토큰들을 모아논 배열
next_token=-1  #토큰 코드 
charClass=0 #LETTER 인가? DIGIT인가? UNKNOWN 인가? EOF 인가?
error_state="" # OK,warning,error 중 하나 + 에러설명
identifier={} #사용된 식별자들 저장
sentence=[] # 수정한 statement 문장 저장
id_count=0 #한 문장에서 식별자 개수
const_count=0 #한 문장에서 상수 개수
op_count=0 #한 문장에서 연산자 개수
sentence_front=0 # 한 문장의 시작
sentence_last=0 # 한 문장의 끝


#상수들 정의
LETTER=0
DIGIT=1
UNKNOWN=2
EOF=99
token_code={"error":-1,"incorrect_IDENT":-2,"INT_LIT":10, "IDENT":11, "ASSIGN_OP":20, ":=":20,"ADD_OP":21, "+":21,"SUB_OP":22,"-":22,"MULT_OP":23, "*":23,"DIV_OP":24, "/":24, "LEFT_PAREN":25, "(":25,")":26,"RIGHT_PATERN":26,":=":31,":":32,"=":33,";":40}
reserve_word=["do","for","while","case","default","else","if","switch","break","continue","goto","return","char","double","float","int","long","short","enum","const","sizeof","void","typedef","static","extern","auto","struct"] #C언어 예약어들

#함수들 정의
#(1) 어휘분석 과 관련된 함수들
def getchar(): #문자 하나를 입력받는 함수
    global next_char,charClass,code_position
    if(code_position<len_code): # 읽을 코드가 남아 있으면
        next_char=code[code_position] 
        code_position+=1
        if(next_char.isalpha()): # 알파벳인가?
            charClass=LETTER
        elif(next_char.isdigit()): #정수인가?
            charClass=DIGIT
        elif(next_char=="_"): #_은 이름에 들어갈 수 있음.
            charClass=LETTER 
        else: #그외 문자 
            charClass=UNKNOWN   
    else: #코드를 다 읽은 경우
        charClass=EOF
        next_char="EOF"
        
def getNonBlank(): # 공백 무시 함수
    while(next_char.isspace()):
        getchar()

def addChar(): #lexeme에 문자 하나 추가
    global lexeme
    lexeme+=next_char

def lookup(ch): #unknown 문자 Ch가 어떤 type에 속하는지 확인하는 작업
    global next_token,charClass,code_position,next_char
    if(ch=="("):
        addChar()
        next_token=token_code["("]
    elif(ch==")"):
        addChar()
        next_token=token_code[")"]
    elif(ch=="+"):
        addChar()
        next_token=token_code["+"]
    elif(ch=="-"):
        addChar()
        next_token=token_code["-"]
    elif(ch=="/"):
        addChar()
        next_token=token_code["/"]
    elif(ch=="*"):
        addChar()
        next_token=token_code["*"]
    elif(ch==";"):
        addChar()
        next_token=token_code[";"]
    elif(ch==":"):
        addChar()
        save_class=charClass # token이 : 만 있는 경우 대비
        save_position=code_position
        save_next=next_char
        getchar()
        if(next_char=="="):
            addChar()
            next_token=token_code[":="]
        else:
            charClass=save_class  # :=이 아닌 경우 이전 상태로 복구 작업
            charClass=save_class
            code_position=save_position
            next_char=save_next
            next_token=token_code[":"]
    elif(ch=="="):
        addChar()
        next_token=token_code["="]
    else:
        addChar()
        next_token=token_code["error"] #이상한 문자 입력됨.
  
def lexical(): # 코드를 lexeme으로 분리하는 함수
    global next_token,lexeme,token_count
    lexeme=""
    getNonBlank()
    if(charClass==LETTER): #문자열인 경우
        addChar()
        getchar()
        while(charClass==LETTER or charClass==DIGIT): #문자열 or 정수일 때 반복 
            addChar()
            getchar()
        next_token=token_code["IDENT"]
        if(lexeme in reserve_word): # 식별자는 예약어랑 동일한 이름을 가지면 안됨.
            next_token=token_code["incorrect_IDENT"]   
        
    elif(charClass==DIGIT):  #정수 인 경우
        addChar()
        getchar()
        while(charClass==DIGIT): #정수일 때 계속 반복
            addChar()
            getchar()
        next_token=token_code["INT_LIT"]
        while(charClass==LETTER or charClass==DIGIT): #1qer2 와 같은 식별자는 C에서 허용 안함(잘못된 식별자 처리)
            addChar()
            getchar()
            next_token=token_code["incorrect_IDENT"]
    elif(charClass==UNKNOWN):
        lookup(next_char)
        getchar()
    elif(charClass==EOF):
        next_token=EOF
        lexeme="EOF"

    token_string.append(lexeme) #lexeme을 token 배열에 추가
    token_count+=1
    #print("next token is", next_token, "next lexeme is",lexeme) #디버깅 확인용
    return next_token 

#(2) 구문 분석 과 관련된 함수들
def initialize(): #각 문장 실행시마다 필요한 요소를 초기화 시키는 함수.
    global error_state,sentence,id_count,const_count,op_count,sentence_front
    error_state="" #상태 초기화
    sentence=[] # statement 문장 초기화
    id_count=0 #한 문장에서 식별자 개수 초기화
    const_count=0 #한 문장에서 상수 개수 초기화
    op_count=0 #한 문장에서 연산자 개수 초기화
    sentence_front=token_count-1

def printinfo(): # 분석한 문장, 각 요소의 개수, error 상태를 출력하는 함수
    global error_state
    
    if(error_state==""):
        error_state+="(OK)\n"
    
    print("<프로그램에 적힌 코드> " ,end="") # 읽은 코드 그대로 출력
    for i in token_string[sentence_front:sentence_last]:
        print(i,end=" ")
    print()
    
    if("Warning" in error_state): #수정한 문장이 있는 경우 수정한 코드 출력
        print("<수정한 코드> " ,end="")
        for i in sentence:
            print(i,end=" ")
        print()
    print("ID:",id_count,"; CONST:",const_count,"; OP:",op_count,";")

    print(error_state,end="")

def print_indent_value(): #식별자 값 출력
    print("Result ==> ", end="")  #최종 연산후 식별자들의 값 출력
    for key,value in identifier.items():
        print(key,":",value,";",end=" ") 
    print()
    
def statements(): # statements -> <statement> {; <statement>}
    global error_state,sentence,sentence_last,sentence_front
    getchar()
    lexical()
    statement()
    #print(token_count) # 디버깅용 token 개수 확인
    if(next_token!=EOF): 
        if(next_token!=token_code[";"]): #;가 누락 된 경우
            error_state+="(Warning) ; 입력 누락. ; 입력 추가\n"      
        else:
             lexical()
        sentence.append(';')
        sentence_last=token_count-1 #마지막 토큰은 다음 문장거이므로 하나 빼줘야 함.    
        
    
    printinfo() # 파싱 결과 출력
    
    while(next_token!=EOF): # EOF가 나올 떄까지 무한 반복
  
        initialize()
        statement()
        if(next_token!=EOF): 
            if(next_token!=token_code[";"]):
                error_state+="(Warning) ; 입력 누락. ; 입력 추가\n"
            else:
                lexical()       
            sentence.append(';')   
        
        sentence_last=token_count-1
        printinfo()
     
    print_indent_value() # 최종 식별자 값 출력


def statement(): #<statement> -> <ident> := <expression>
    global error_state,id_count
    if(next_token== token_code["IDENT"]):
        variable=token_string[-1]
        id_count+=1
    elif(next_token==token_code["incorrect_IDENT"]):
        variable=token_string[-1] 
        id_count+=1
        error_state+="(Error) C언어에 적합하지 않은 식별자 이름.("+variable+") 식별자 이름 변경 필요!!\n"  
    else:
        sentence.append(token_string[-1])
        error_state+="(Error) 불가능한 문법 사용\n"
        lexical()
        return 
    
    sentence.append(variable)
    lexical()
    
    if(next_token==token_code[":="]):
        lexical()
    elif(next_token==token_code[":"]):
        error_state+="(Warning) :만 입력됨, := 입력으로 변경\n"
        lexical()
    elif(next_token==token_code["="]):
        error_state+="(Warning) =만 입력됨, := 입력으로 변경\n"
        lexical()
    else:
        error_state+=("(Warning) 문법 위배, :=입력 추가 \n")  
    
    sentence.append(":=")
    
    if(next_token == token_code[";"]): # ex) A:= ; 인 경우
        error_state+="(Warning) 대입 연산자 뒤에 expression이 없음. 0을 추가 시킴."+variable+"은 0으로 초기화\n"
        sentence.append(0)
        identifier[variable]=0
        return 
    
    get_value=expr()
    identifier[variable]=get_value #식별자에 값 대입
        
def expr(): #<expression> -> <term> {(+|-) <term>}
    global error_state,sentence,op_count,const_count
    total=0
    save="+"
    if(next_token == token_code["+"] or next_token == token_code["-"]): # ex) A:=+3과 같은 경우 A:=0+3으로 변경'
        error_state+="(Warning) iden:="+token_string[-1]+"숫자 구조. iden:= 0 "+token_string[-1]+"숫자 구조로 변경.\n" 
        save=token_string[-1]
        sentence.append("0")
        op_count+=1
        const_count+=1
        lexical()
        while(next_token == token_code["+"] or next_token == token_code["-"]):
            if(next_token == token_code["+"] ):
                if(save=="+"):
                    error_state+="(Warning) 중복 연산자(+) 발생 ++ 이므로 +로 변경\n"                
                    save="+"
                else:
                    error_state+="(Warning) 중복 연산자(+) 발생 -+ 이므로 -로 변경\n"
                    save="-" 
            elif(next_token == token_code["-"]):
                if(save=="-"):
                    error_state+="(Warning) 중복 연산자(-) 발생 -- 이므로 +로 변경\n"
                    save="+"
                else:
                    error_state+="(Warning) 중복 연산자(+) 발생 -+ 이므로 -로 변경\n"
                    save="-"
                    
            lexical()

        if(next_token==token_code[';']): # A=1+; 와 같은 경우 A=1+0;으로 변경
            error_state+="(Warning)"+save+" 뒤에 피연산자 미 입력. 0 자동 추가 \n" 
            sentence.append(0)
            const_count+=1
            return total       
        
        sentence.append(save)
        
    operand1=term()
    #print(total, operand1)
    if(operand1!="Unknown"):
        if(save=="+"):
            total+=operand1
        else:
            total-=operand1
    else: 
        total="Unknown"
        
    while(next_token == token_code["+"] or next_token == token_code["-"]):
        save=token_string[-1] # 연산자 확인을 위한 임시 저장
        op_count+=1
        lexical()
        while(next_token == token_code["+"] or next_token == token_code["-"]):
            if(next_token == token_code["+"] ):
                if(save=="+"):
                    error_state+="(Warning) 중복 연산자(+) 발생 ++ 이므로 +로 변경\n"                
                    save="+"
                else:
                    error_state+="(Warning) 중복 연산자(+) 발생 -+ 이므로 -로 변경\n"
                    save="-" 
            elif(next_token == token_code["-"]):
                if(save=="-"):
                    error_state+="(Warning) 중복 연산자(-) 발생 -- 이므로 +로 변경\n"
                    save="+"
                else:
                    error_state+="(Warning) 중복 연산자(+) 발생 -+ 이므로 -로 변경\n"
                    save="-"
                
            lexical()
        
 
        sentence.append(save)  
        if(next_token==token_code[';']):
            error_state+="(Warning)"+save+" 뒤에 피연산자 미 입력. 0 자동 추가 \n"  #0은 덧셈과 뺄셈의 결과에 영향을 안주므로
            sentence.append(0)
            const_count+=1
            return total       
        
        operand2=term()
        if(total!="Unknown" and operand2!="Unknown"): # Unknown (+/-) 상수 = Unknown 으로 취급
            if(save=="+"):
                total+=operand2
            elif(save=="-"):
                total-=operand2
        else:
            total="Unknown"
    
    return total #계산된 값 부모 노드로 전달
            
def term(): #<term> -> <factor> {(*|/) <factor>}
    global error_state,sentence,op_count,const_count
    while(next_token == token_code["*"] or next_token == token_code["/"]): # ex) *<factor> 은 문법 위배
        error_state+="(Warning) 잘못된 "+token_string[-1]+"의 삽입. 삭제함 \n"
        lexical()
    total=1
    operand1=factor()
    total=operand1
    
    while(next_token == token_code["*"] or next_token == token_code["/"]):
        save=token_string[-1]
        sentence.append(save)
        op_count+=1
        lexical()
        while(next_token == token_code["*"] or next_token == token_code["/"]): #*/ 와 같이 연달아 입력된 경우 맨 앞에 걸 선택(* 선택)
            error_state+="(Warning) 잘못된 "+token_string[-1]+"의 삽입."+token_string[-1]+"삭제함\n"
            lexical()
        
        if(next_token == token_code[";"]):
            error_state+="(Warning)"+save+"뒤에 피연산자가 입력되지 않음. 1을 자동 추가 \n" #1은 나눗셈과 곱셈의 결과에 영향을 안주므로
            sentence.append(1)
            const_count+=1
            return total   
        
        operand2=factor()
        
        if(total!="Unknown" and operand2!="Unknown"):
            if(save=="*"):
                total*=operand2
            elif(save=="/"):
                if(operand2==0): #0으로 나누는 건 불가능
                    error_state+="(Error) 0으로 나누기 시도. 결과값은 Unknown으로 반환\n"
                    total="Unknown"
                else:
                    total/=operand2
        else: # Unknown/ 상수 = Unknown
            total="Unknown"
    
    return total # 부모 노드에 연산 값 전달.
    
def factor(): #<factor> -> ( <expression> ) | 식별자 | 정수 상수
    global error_state,sentence,const_count,id_count
    if(next_token == token_code["IDENT"] ):
        sentence.append(token_string[-1])
        id_count+=1
        if(token_string[-1] in identifier): # 식별자가 존재하고 그 값이 정의 된 적 있으면
            save=token_string[-1]
            lexical()
            
            if(identifier[save]!="Unknown"):
                return float(identifier[save])
            else:
                return identifier[save]
            
        else: # 정의 된 적 없는 변수 사용 시도
            error_state+="(Error) 정의되지 않은 변수("+token_string[-1]+")이 참조 됨. Unknown 반환\n"
            identifier[token_string[-1]]="Unknown"
            lexical()
            return "Unknown"
    elif(next_token == token_code["incorrect_IDENT"]):
        sentence.append(token_string[-1])
        id_count+=1 # 이름이 잘못된 식별자도 파싱과정 중엔 식별자 취급
        if(token_string[-1] in identifier): # 잘못된 이름의 식별자가 존재하고 그 값이 정의 된 적 있으면
            save=token_string[-1]
            lexical()
            return float(identifier[save])

        else: # 정의 된 적 없는 변수 사용 시도
            error_state+="((Error) C언어에 적합하지 않은 식별자 이름.(",token_string[-1],") 식별자 이름 변경 필요!!  정의되지 않은 변수("+token_string[-1]+")이 참조 됨. Unknown 반환\n"
            id_count+=1
            lexical()
            return "Unknown"
    elif(next_token == token_code["INT_LIT"]):
            sentence.append(token_string[-1])
            save=token_string[-1]
            const_count+=1
            lexical()
            return int(save)
    
    elif(next_token== token_code["LEFT_PAREN"]):
        sentence.append('(')
        lexical()
        value=expr()
        if(next_token== token_code["RIGHT_PATERN"]):
            sentence.append(')')
            lexical()
            return value
        else:
            error_state+="(Warning) ) 가 안 닫힘. ) 추가.\n"
            sentence.append(")")
            return value           
    elif(next_token==token_code['-']):
        save="-"
        lexical()
        while(next_token == token_code["+"] or next_token == token_code["-"]):
            if(next_token == token_code["+"] ):
                if(save=="+"):
                    error_state+="(Warning) 중복 연산자(+) 발생 ++ 이므로 -로 변경\n"                
                    save="+"
                else:
                    error_state+="(Warning) 중복 연산자(-) 발생 -+ 이므로 -로 변경\n"
                    save="-" 
            elif(next_token == token_code["-"]):
                if(save=="-"):
                    error_state+="(Warning) 중복 연산자(-) 발생 -- 이므로 +로 변경\n"
                    save="+"
                else:
                    error_state+="(Warning) 중복 연산자(+) 발생 -+ 이므로 -로 변경\n"
                    save="-"
                
            lexical()
        
        
        if (next_token == token_code["INT_LIT"]):
            if(save=='+'):
                error_state+="(Warning)  + 이므로 + 삭제\n"
                sentence.append(token_string[-1])
                num=token_string[-1]
                lexical()
                return int(num)
            elif(save=="-"):
                error_state+="(Warning) 상수로 음수를 이용\n"
                
                num="-"+token_string[-1]
                sentence.append(num)
                lexical()
                return int(num)
            
        else:
            error_state+="(Error) 허용되지 않은 문법 입력. Unknown 반환\n"
            return "Unknown" 
    
    else:
        error_state+="(Error) 허용되지 않은 문법 입력. Unknown 반환\n"
        return "Unknown"
    
   
# main() 프로그램 시작

if(len(sys.argv)==1): #파일 입력이 안 주어진 경우
    file_name=input("사용할 파일의 이름을 입력하세요:")
else:
    file_name=sys.argv[1] #command line parameter로 입력된 파일 이름 1개

file=open(file_name,"r",encoding="UTF8")

code=file.read() #파일에서 적혀 있는 모든 내용을 읽어옴.
len_code=len(code); #코드의 총 길이

statements()

#print(token_string) #디버깅 확인용(token 잘 분리 되었는지 확인용)