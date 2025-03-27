from sqlalchemy import create_engine,text

class databases : 
    def __init__(self):
        self.IP = ''
        self.ID = ''
        self.PW = ''
        self.PORT = 3306

        self.DBNAME     = 'miniproject3'
        self.TABLE_NAME = 'Users'  
        self.PROTOCAL   = 'mysql+pymysql' 

    def create_db(self) : 
        db_url = f'{self.PROTOCAL}://{self.ID}:{self.PW}@{self.IP}:{self.PORT}/{self.DBNAME}'
        engine = create_engine(db_url)
        self.conn = engine.connect()
        return self.conn
    
    def save_resume_chat(self,chat_id: int, question: str, answer: str) : 
        query = text(f'INSERT INTO Chat_Resume (chat_id, question, answer) VALUES ({chat_id}, "{question}", "{answer}")')
        print(query)
        self.conn.execute(query)
        self.conn.commit()
    
    def save_interview_chat(self,chat_id: int, question: str, answer: str) : 
        query = text(f'INSERT INTO Chat_Interview (chat_id, question, answer) VALUES ({chat_id}, "{question}", "{answer}")')
        self.conn.execute(query)
        self.conn.commit()
    
    def close_db(self) : 
        self.conn.close()

if __name__ == "__main__" : 
    new_db = databases()
    conn = new_db.create_db()
    new_db.close_db()