import socket
import pymysql
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
import threading
import os
import deeplearning as dl

lock = threading.Lock()

class Socket():
    def __init__(self):
        # 데이터베이스 연결
        self.db = pymysql.connect(host='localhost',
                                  user='root',
                                  password='1234',
                                  db='testdb',
                                  charset='utf8')
        self.cursor = self.db.cursor(pymysql.cursors.DictCursor)
        # 카메라, 분부기 등록 날짜
        self.registerDate= datetime.datetime.now()
        # 인공지능 기반 살균 시작 날짜
        self.startDate = (self.registerDate+ datetime.timedelta(days=2)).strftime('%Y=%m-%d')
        self.CAMlist=[]  # 카메라 라즈베리파이 고유 아이디 등록
        self.STElist=[]  # 살균기 라즈베리파이 고유 아이디 등록
        self.sched = BackgroundScheduler(timezone="Asia/seoul")
        self.sched.add_job(self.cleanAlgorithm, 'cron', hour=0)  # 인공지능 살균 스케줄러

        self.fiveMin_data=[[],[],[],[],[],[],[],[],[]]
        self.trainResult_data=[[],[],[],[],[],[],[],[],[]]
        self.cleantime=[[],[],[],[],[],[],[],[],[]]
        self.train_data=[]
        self.cname = ''
        self.ccheck = False

        self.STECLEAN=[]

    def get_CAMlist(self):
        return self.CAMlist

    def get_sensor(self):
        pass

    def command_clean(self, id):
        pass

    def get_document(self, id):
        pass

    # 인공지능 기반 살균 알고리즘
    def cleanAlgorithm(self):
        # 학습데이터 검증
        self.verificationData()

        # 전처리 - 5분단위로
        self.make_fiveMin()

        # 학습
        for i, v in enumerate(self.CAMlist):
            x = self.fiveMin_data[i]
            y = self.fiveMin_data[i]
            now = datetime.datetime.today().weekday()
            if now==5 or now==6:
                if not os.path.exists('model/' + v[0][0] + '/weekend'):
                    os.makedirs('model/' + v[0][0] + '/weekend')
                    dl.make_model(x, y, 'model/' + v[0][0] + '/weekend/weekend')
                else:
                    dl.retrain_model(x, y, 'model/' + v[0][0] + '/weekend/weekend')
            else:
                if not os.path.exists('model/' + v[0][0] + '/weekly'):
                    os.makedirs('model/' + v[0][0] + '/weekly')
                    dl.make_model(x, y, 'model/' + v[0][0] + '/weekly/weekly')
                else:
                    dl.retrain_model(x, y, 'model/' + v[0][0] + '/weekly/weekly')

        # 딥러닝 모델에서 결과 받아오기

        # 받아온 학습결과기반 살균 알고리즘


        # 살균알고리즘 기반 살균 시간 저장
        self.save_cleantime()


    # 살균알고리즘 기반 살균 시간 저장 - 미완
    def save_cleantime(self):
        now = datetime.datetime.now()

        dStart = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
        dend = datetime.datetime(now.year, now.month, now.day, 23, 55, 0)

        timelist = []
        while 1:
            str = dStart.strftime('%Y-%m-%d %H:%M:%S')
            timelist.append(str)
            dStart = dStart + datetime.timedelta(seconds=300)
            if (dStart == dend):
                str = dStart.strftime('%Y-%m-%d %H:%M:%S')
                timelist.append(str)
                break

    # 데이터 전처리(5분마다 처리)
    def make_fiveMin(self):
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)

        sql_sel = "SELECT cnt FROM test_table2 where id = %s and time between %s and %s"

        for i, name in enumerate(self.CAMlist):
            dStart = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
            dend = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
            while 1:
                next = dStart + datetime.timedelta(seconds=300)
                self.cursor.execute(sql_sel, (name, dStart, next))
                res = self.cursor.fetchall()
                data0=0
                data1=1
                for v in res:
                    if v['cnt']==1:
                        data1+=1
                    else:
                        data0+=0
                if data1/(data1+data0)>=80:
                    self.fiveMin_data[i].append(1)
                else:
                    self.fiveMin_data[i].append(0)
                next_str = next.strftime('%Y-%m-%d %H:%M:%S')
                dStart = dStart + datetime.timedelta(seconds=300)
                if (dStart == dend):
                    next = dStart + datetime.timedelta(seconds=300)
                    self.cursor.execute(sql_sel, (name, dStart, next))
                    res = self.cursor.fetchall()
                    data0 = 0
                    data1 = 1
                    for v in res:
                        if v['cnt'] == 1:
                            data1 += 1
                        else:
                            data0 += 0

                    if data1 / (data1 + data0) >= 80:
                        self.fiveMin_data[i].append(1)
                    else:
                        self.fiveMin_data[i].append(0)
                    next_str = next.strftime('%Y-%m-%d %H:%M:%S')
                    break

    # 학습 데이터 검증
    def verificationData(self):
        now = datetime.datetime.now()
        now = now - datetime.timedelta(days=1)
        formatted_data = now.strftime('%Y-%m-%d')

        time1 = formatted_data + ' 00:00:00'
        time2 = formatted_data + ' 23:59:59'
        for name in self.CAMlist:
            # 특정 하루 기간 동안 저장된 데이터 개수 알아내기
            sql = "SELECT count(*) FROM test_table2 where id = %s and time between %s and %s"

            self.cursor.execute(sql, (name, time1, time2))
            res = self.cursor.fetchall()
            # 86400개 데이터가 아니라면 그날을 1초 단위로 반복하면서 데이터가 없다면 '0'으로 삽입
            if res[0]['count(*)'] != 86400:
                dStart = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
                dEnd = dStart + datetime.timedelta(days=1)
                while 1:
                    sql = "SELECT count(*) FROM test_table2 where id = %s and time = %s"
                    intime = dStart.strftime('%Y-%m-%d %H:%M:%S')
                    self.cursor.execute(sql, (name, intime))
                    res = self.cursor.fetchall()
                    if res[0]['count(*)'] == 0:
                        lock.acquire()
                        self.cursor.execute('insert into test_table2 values(%s,%s,%s)', (name, intime, '0'))
                        self.db.commit()
                        lock.release()
                    dStart = dStart + datetime.timedelta(seconds=1)
                    if dStart == dEnd:
                        break

    # 살균 명령 - 미완
    def commandClean(self):
        while True:
            now = datetime.datetime.now()  # 현재 날짜 얻어오기
            formatted_data = now.strftime('%Y=%m-%d %H:%M')  # 현재 시간 문자열 포맷팅
            for i, v in self.STElist:
                for j in self.cleantime[i]:
                    if formatted_data==j:
                        self.cname=self.STElist[i]
                        self.ccheck=True

    # 카메라 라즈베리파이와 통신해서 데이터 삽입
    def cam_handler(self, conn, addr, name, terminator="bye"):
        pri_date=''
        while True:
            data = conn.recv(1024) # 데이터 받아옴
            if data == b"exit":
                break
            now = datetime.datetime.now() # 현재 날짜 얻어오기
            formatted_data = now.strftime('%Y=%m-%d %H:%M:%S') # 현재 시간 문자열 포맷팅
            if formatted_data==pri_date: # 이전에 저장한 시간 데이터와 같으면 패스
                continue
            pri_date=formatted_data
            print(name, formatted_data, data)
            lock.acquire()
            self.cursor.execute('insert into test_table2 values(%s,%s,%s)', (name, formatted_data, data)) # 데이터 삽입
            self.db.commit()
            lock.release()

    # 살규기 라즈베리파이와 통신해 여러 명령 전송 - 미완
    def clean_handler(self, conn, addr, name, terminator="bye"):
        while True:
            if self.cname==name and self.ccheck:
                conn.send('clean'.encode(encoding='utf_8', errors='strict'))
                data = conn.recv(1024)
                self.cname=''
                self.ccheck=False
                if data == b"exit":
                    break
                elif data[0:12] == "cleanResult":
                    pass


    def run_server(self, host='', port=8888):
        check=False
        with socket.socket() as sock:
            sock.bind((host, port))
            while True:
                # 현재 시간과 인공지능 살균 시작 시간이 같으면 스케줄러  시작
                now = datetime.datetime.now()
                nowstrdate = now.strftime('%Y=%m-%d')
                if self.startDate==nowstrdate and check==False:
                    self.sched.start()
                    check=True
                # 소켓 스레드 통신
                sock.listen(5)
                conn, addr = sock.accept()
                id = conn.recv(1024).decode(encoding='utf_8', errors='strict')
                if id[0:3]=='CAM': # 통신대상이 카메라일 경우
                    temp = id.split(',')
                    id = temp[0]
                    name = temp[1]
                    os.mkdir('model/'+id)
                    temp_list = [id, name]
                    self.CAMlist.append(temp_list)
                    self.CAMlist.sort(key=lambda x: x[0][4])
                    print(self.CAMlist)
                    t = Thread(target=self.cam_handler, name=id, args=(conn, addr, id))
                    t.start()
                elif id[0:3]=='STE': # 통신대상이 살균기일 경우
                    self.STElist.append(id)
                    self.STElist.sort(key=lambda x: x[4])
                    self.STECLEAN.append(False)
                    t = Thread(target=self.clean_handler, name=id, args=(conn, addr, id))
                    t.start()
            sock.close()

    def fininsh(self):
        #self.scheduler.shutdown()
        #self.conn.close()
        self.cursor.close()
        self.db.close()
        print('socket disconnect')