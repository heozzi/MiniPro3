from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types,F
from aiogram.types import Update
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
from db import databases,text
from rag import RAG
import os

usedb = databases()
conn = usedb.create_db()

OpenAI_API_KEY = ""
os.environ["OPENAI_API_KEY"] = OpenAI_API_KEY

userag = RAG("Data/",OpenAI_API_KEY)

#define
OPTION_1 = "자소서 컨펌"
OPTION_2 = "모의 면접 진행"
OPTION_3 = "회사 및 직무 입력"

# 텔레그램 봇 토큰
TOKEN = ""
# 텔레그램의 웹훅 (HTTP는 불가, 그래서 HTTPS로 해야함)
'''
1. pip install ngrok -> 설치
2. https://dashboard.ngrok.com/signup -> 회원가입
3. https://dashboard.ngrok.com/get-started/your-authtoken -> 토큰 발행
4. config add-authtoken [토큰]
5. ngrok http 8000 -> 실행 (파이썬 가상환경이 세팅이 된 터미널에서 실행)
6. Forwarding 주소 확인 후 웹훅에 넣기
'''
WEBHOOK_URL = "/webhook"

# FastAPI 앱 생성
app = FastAPI()

'''
telegram-bot 설치해서 진행
fastapi에서 사용하고 싶으면 aiogram 에서 라이브러리 사용
https://aiogram.dev/
'''
# aiogram Bot & Dispatcher
bot = Bot(token=TOKEN,  # 봇 토큰 설정
          default=DefaultBotProperties(parse_mode="HTML") # 텔레그램 메세지를 HTML 허용
          )
# 봇이 모든 이벤트를 관리하는 컨트롤 객체(메세지,명령어,버튼 클릭 등등등)
dp = Dispatcher()

# 로그 설정
logging.basicConfig(level=logging.INFO)

# 웹훅 엔드포인트 (텔레그램이 이 URL로 요청을 보냄)
@app.post("/webhook")
async def telegram_webhook(update: dict):
    telegram_update = Update.model_validate(update)  # aiogram 3.x에서 사용
    await dp.feed_update(bot, telegram_update)  # aiogram 디스패처에 전달
    return {"status": "ok"}


# 버튼 생성
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=OPTION_1), KeyboardButton(text=OPTION_2), KeyboardButton(text=OPTION_3)]
    ],
    resize_keyboard=True  # 키보드 크기 조절
)

# /start 핸들러 (버튼 포함)
@dp.message(F.text.lower() == "/start") 
async def start_command(message: types.Message):
    chat_id = message.chat.id

    # chat_id가 존재하는지 체크
    result = conn.execute(text(f"select * from Users where chat_id = {chat_id};"))

    # 존재하지 않으면 DB에 등록
    if not result.all() : 
        conn.execute(text(f"insert into Users(chat_id) value ({chat_id});"))
        conn.commit()
    else :
        # 기존 유저면 0으로 초기화
        conn.execute(text(f"update Users set switch=0 where chat_id = {chat_id};"))
        conn.commit()

    ment = '''안녕하세요! 원하는 옵션을 선택하세요.
    옵션을 선택하지 않으면 진행 할 수 없습니다.

    또한 옵션을 바꾸지 않으면 원활한 답변이 안될 수 있는 점 유의해주세요
    EX) 자소서 도중 모의 면접을 하고 싶으면 도중에 면접 옵션을 클릭하셔서 변경해야 합니다.
    '''
    await message.answer(ment, reply_markup=keyboard)

# 메세지가 오면 먼저 처리하는 핸들러
@dp.message()
async def handle_buttons(message: types.Message):
    # chat_id 가져오기
    chat_id = message.chat.id
    # DB에 chat_id값 가져오기
    result = conn.execute(text(f"select * from Users where chat_id = {chat_id};"))
    # 스위치는 [0][-1] 위치에 속함 (all() -> ([1,0]) 으로 반환됨)
    sw = result.all()[0][-1]

    if message.text == OPTION_1:
        answer_ex = f'''
        {OPTION_1}을 선택하셨습니다!
        
        데이터를 보낼 때 여러 가지를 한 번에 보내주세요!
        Q : 질문(EX : 지원동기 700자 입력해주세요)
        A : 답변 ...

        Q : 질문(EX : 입사 후 포부 700자 입력해주세요)
        A : 답변 ...

        Q : 질문(EX : 나의 강점 700자 입력해주세요)
        A : 답변 ...

        형식으로 입력 부탁드립니다!
        '''

        # 스위치 1번으로 자소서 함수를 호출 진행
        conn.execute(text(f"update Users set switch=1 where chat_id = {chat_id};"))
        conn.commit()

        await message.answer(answer_ex)
    elif message.text == OPTION_2:
        answer_ex = f'''
        {OPTION_2}을 선택하셨습니다!
        Q : 1분 자기소개를 부탁드립니다!
        '''
        # 스위치 2번으로 면접 함수를 호출 진행
        conn.execute(text(f"update Users set switch=2 where chat_id = {chat_id};"))
        conn.commit()

        await message.answer(answer_ex)

    # 채팅으로 입력이 되면 진행
    # 채팅이 없을 경우 message.text는 None으로 표시
    elif message.text == OPTION_3:
        await message.answer("회사 및 직무를 입력해주세요(SK쉴더스/프론트엔드)")
        conn.execute(text(f"update Users set switch=3 where chat_id = {chat_id};"))
        conn.commit()

    elif sw == 3:
        company,job = message.text.split('/')
        userag.setting(company=company,job=job)
        await message.answer(f"회사는 {company}이고 직무는 {job}입니다.")

        conn.execute(text(f"update Users set switch=0 where chat_id = {chat_id};"))
        conn.commit()

    elif sw == 0 :
        answer_ex = '''옵션을 선택해주세요
        옵션을 선택하지 않을시 해당 기능을 사용할 수 없습니다.
        '''
        await message.answer(answer_ex)

    elif message.text != None and sw!=2: 
        userag.setting(message.text)
        userag.searching('''합격 자소서, 합격자 면접, 업계 동향, 구인 데이터를 참고하여, 
                                자소서 작성 피드백에 유용한 핵심 인사이트를 간략히 요약해줘.''')
        
        userag.add_searching(f"{userag.company} 관련 산업 뉴스, 최신 동향, 전략 및 이슈","[산업 뉴스 참고]:")
        userag.make_chain1()
        userag.make_chain2()
        # userag.make_chain3()
        answer = userag.run_resume()

        question = message.text
        # usedb.save_resume_chat(chat_id,question,answer)
        await message.answer(answer)
    else : 

        if message.text != None : 
            userag.voice_text = message.text
        else : 
            # 오디오 파일 입력시 message.voice에 파일이 들어온다
            file = await bot.get_file(message.voice.file_id)
            file_path = file.file_path

            # 다운로드 진행
            # 추후에는 시간 or id값으로 진행
            filename = f"{chat_id}.ogg"
            await bot.download_file(file_path, filename)
            userag.use_whisper(filename)

        # GPT 대답 저장
        answer = userag.run_interview()

        # DB에 값 저장
        # 에러 발생 https://sqlalche.me/e/20/f405
        question = userag.que_text[-1]
        usedb.save_interview_chat(chat_id,question,message.text)
        
        # 새로운 질문 할당
        userag.new_question()
        new_question = userag.que_text[-1]
        
        await message.answer(answer)
        await message.answer(new_question)

# 서버 시작 시 웹훅 설정
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    userag.setting(resume="",company="",job="") # 초기값 설정

# 서버 종료 시 웹훅 삭제
@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()
    usedb.close_db()