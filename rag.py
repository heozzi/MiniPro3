# from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from llama_index.core import  SimpleDirectoryReader
from llama_index.core import GPTVectorStoreIndex
from openai import OpenAI
from groq import Groq

GROQ_API_KEY=''

class RAG :
    def __init__(self,path,OpenAI_API_KEY):
        '''
        GPT,LLM,Whisper 초기 세팅 함수 

        Args:
           path : 참조할 문서 위치 
           OpenAI_API_KEY : OpenAPI_KEY
        '''

        # self.OpenAI_API_KEY=OpenAI_API_KEY
        self.openai_client = OpenAI(api_key=OpenAI_API_KEY)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=1.0)
        self.documents = SimpleDirectoryReader(path).load_data()
        index = GPTVectorStoreIndex.from_documents(self.documents)
        self.query_engine = index.as_query_engine()
        self.client = Groq(api_key=GROQ_API_KEY)
        self.que_text = ["1분 자기소개를 부탁드립니다!"]
        self.result = ""
        self.resume = ""

    def setting(self,resume=None,company=None,job=None) : 
        '''
        회사정보, 직무, 자소서를 세팅하는 함수

        Args:
           company : 회사 이름 
           job : 직무 정보
           resume : 첨삭받을 자소서

        '''
        if company != None : 
            self.company = company
        if job != None : 
            self.job = job
        if resume != None : 
            self.resume = resume
        pass

    # 검색 기능은 3개 정도 
    def searching(self,text) : 
        '''
        RAG 기능을 사용한 쿼리 질의를 저장하는 함수 

        Args:
           text : 참조할 텍스트 내용

        '''
        reference_query = (text)
        self.result = str(self.query_engine.query(reference_query))
    
    def add_searching(self,text,concat_text) : 
        ''' 
        RAG에 추가 내용 넣기  

        Args:
           text : 참조할 텍스트 내용
           concat_text : 두 텍스트 사이에 넣을 텍스트
        '''
        reference_query = (text)
        self.result += "\n\n"+concat_text+str(self.query_engine.query(reference_query))

    def init_chain(self) : 
        # === 자소서 분석 체인 프롬프트 템플릿 === 
        prompt = PromptTemplate( input_variables=["참고자료"], 
                                     template=""" 이전 대화 내용을 무시하고, 아래에 제공된 정보만을 기반으로 분석을 수행해 주세요. 이후에 입력하는 내용을 기반으로 자소서 분석, 조언, 피드백을 제공해주세요. 
                                     -------------------------------------- {참고자료} -------------------------------------- """ )
        init_chain = LLMChain(llm=self.llm, prompt=prompt)
        init_chain.run(
            참고자료=self.result)

    def make_chain1(self) :
        '''
        LLM Chain 설정하는 함수 
        '''
        self.init_chain() # 초기화 
        
        
        prompt = PromptTemplate(
            input_variables=["자소서내용", "참고자료", "회사", "직무"],
            template="""
                    사용자가 입력한 자소서 내용은 다음과 같습니다:
                    --------------------------------------
                    {자소서내용}
                    --------------------------------------
                    아래의 참고 자료는 합격 자소서, 면접 데이터, 업계 동향, 구인 데이터 및 지원 기업 관련 산업 뉴스에서 추출된 인사이트입니다:
                    --------------------------------------
                    {참고자료}
                    --------------------------------------
                    또한, 사용자가 지원하는 회사는 "{회사}"이며 희망 직무는 "{직무}"입니다.
                    위 정보를 종합하여, 다음 사항들을 분석해줘:
                    1. 자소서에 나타난 강점과 약점을 각각 3가지씩 구체적으로 제시
                    2. 자소서 내용이 지원하는 회사와 희망 직무에 얼마나 부합하는지 평가하고, 개선이 필요한 부분(예: 지원 동기, 관련 경험, 역량 표현 등)을 구체적으로 지적
                    3. 최종적으로, 해당 자소서의 지원 적합성 점수를 0부터 10까지의 수치로 산출해줘.
                    예시 출력 형식:
                    - 강점: [예: 문제 해결 능력, 팀워크 등]
                    - 약점: [예: 경험 부족, 구체성 부족 등]
                    - 적합성 평가: [예: 지원 동기 보완 필요 등]
                    - 지원 적합성 점수: [예 : 5/10]
                    """)

        self.analysis_chain = LLMChain(llm=self.llm, prompt=prompt)

    def make_chain2(self) :
        '''
        LLM Chain 설정하는 함수 
        '''
        prompt = PromptTemplate(
                input_variables=["분석결과", "회사", "직무"],
                template="""
                    아래 분석 결과와 지원 정보(지원 회사 및 직무)를 참고하여, 자소서 개선 및 보완을 위한 구체적인 조언을 작성해줘.
                    분석 결과:
                    --------------------------------------
                    {분석결과}
                    --------------------------------------
                    지원 정보:
                    - 지원하는 회사: {회사}
                    - 지원하는 직무: {직무}

                    조언은 실제 자소서에 적용 가능한 수정 방안과 개선 방향을 상세하게 제시하고, 지원 회사와 직무에 맞는 어필 포인트를 반영해줘.
                    그리고 분석결과에서 출력된 점수도 다시 출력해줘.
                    """
            )

        self.advice_chain = LLMChain(llm=self.llm, prompt=prompt)

    def make_chain3(self) :
        '''
        LLM Chain 설정하는 함수 
        '''
        prompt = PromptTemplate(
                input_variables=["조언결과", "회사", "직무"],
                template="""
            아래 조언 결과를 바탕으로, 실제 지원자가 제출할 수 있는 자기소개서 예시를 작성해줘.
            자기소개서는 다음과 같은 구조를 갖추어야 합니다:
            1. **지원동기 및 비전:** 지원 동기, 본인의 비전, 그리고 지원 회사({회사}) 및 직무({직무})와의 시너지를 명확히 서술
            2. **경험 및 역량:** 학습, 동아리/프로젝트 경험, 보유 기술 및 역량을 구체적으로 기술
            3. **강점 및 보완 사항:** 분석된 강점을 부각시키고, 약점을 개선하기 위한 구체적인 실행 계획 제시
            4. **향후 계획:** 입사 후 성장 방향과 목표

            각 항목별로 소제목을 붙여 자기소개서 형식(각 섹션별로 구분)으로 작성해줘.
            아래 조언 결과:
            --------------------------------------
            {조언결과}
            --------------------------------------
            자기소개서 예시:
            """
            )

        self.example_chain = LLMChain(llm=self.llm, prompt=prompt)
    
    def use_whisper(self,filename) : 
        '''
        Whisper를 활용하여 음성파일을 텍스트로 저장

        Args:
           filename : 음성파일 경로+파일명
        '''

        with open(filename, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
                )
        self.voice_text = transcription.text
    
    def run_resume(self) : 
        '''
        LangChain을 활용하여 자소서 첨삭 데이터 얻기 

        Returns:
           첨삭받은 자소서 내용
        '''
    
        analysis_result = self.analysis_chain.run(
            자소서내용=self.resume,
            참고자료=self.result,
            회사=self.company,
            직무=self.job
        )

        advice_result = self.advice_chain.run(
            분석결과=analysis_result,
            회사=self.company,
            직무=self.job
        )
        # example_self_intro = self.example_chain.run(
        #     조언결과=advice_result,
        #     회사=self.company,
        #     직무=self.job
        # )
        
        return advice_result
    

    def run_interview(self) : 
        '''
        LangChain을 활용하여 면접 데이터 얻기

        Returns:
           조언받은 면접 내용
        '''
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content":  """
                                    You must generate a detailed and long answer in korean.
                                    You are an AI assistant.
                                    You will be given a task.
                                    I will give you two article.
                                    One is part of the job seeker's interview.
                                    Another is a index-query-model made from a self-introduction that passed the document screening process
                                    Give feedback on how to fix it to be an appropriate answer for the company.
                                    Answer must be to exclude that the index-query-model was referenced
                                """
                },
                {
                    "role":"user",
                    "content": f'''
                                    구직자 인터뷰 : {self.voice_text}
                                    인덱스 쿼리모델 : {self.result}
                                    회사정보 : {self.company}
                                    직무정보 : {self.job}
                                '''
                }
            ]
        )
        return str(response.choices[0].message.content)
    def new_question(self) :
        text = f'''
        면접 질문을 아래 내용과 중복되지 않게 1개만 만들어줘(한국어로)
        
        [중복내용]
        {self.que_text[-1]}
        '''
        self.que_text.append(str(self.query_engine.query(text)))

