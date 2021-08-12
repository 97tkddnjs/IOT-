import socket
import pymysql
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time
from threading import Thread
import threading

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

        self.cname=''
        self.ccheck=False

        self.fiveMin_data=[[],[],[],[],[],[],[],[],[]]
        self.trainResult_data=[[],[],[],[],[],[],[],[],[]]
        self.train_data=[]

        self.STECLEAN=[]

    # 인공지능 기반 살균 알고리즘
    def cleanAlgorithm(self):
        # 학습데이터 검증
        self.verificationData()

        # 전처리 - 5분단위로
        self.make_fiveMin()

        # 전처리 - 데이터 합치기
        self.make_merge()

        # 학습

        # 학습결과기반 살균 알고리즘

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

    # 데이터 합치기
    def make_merge(self):
        for i in range(len(self.fiveMin_data[0])):
            temp = ''
            for j in range(len(self.CAMlist)):
                temp = str(self.fiveMin_data[j][i]) + temp
            temp = int(temp, 2)
            self.train_data.append(temp)

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
            formatted_data = now.strftime('%Y=%m-%d %H:%M:%S')  # 현재 시간 문자열 포맷팅

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
            conn.send(name.encode(encoding='utf_8', errors='strict'))
            if self.cname==name and self.ccheck:
                print(name)
                time.sleep(1)
                data = conn.recv(1024)

                if data == b"exit":
                    break
                elif data[0:12] == "cleanResult":
                    pass

                now = datetime.datetime.now()
                formatted_data = now.strftime('%Y=%m-%d %H:%M:%S')
                print(name, formatted_data, data)

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
                name = conn.recv(1024).decode(encoding='utf_8', errors='strict')
                if name[0:3]=='CAM': # 통신대상이 카메라일 경우
                    self.CAMlist.append(name)
                    self.CAMlist.sort(key=lambda x: x[4])
                    self.fiveMin_data.append([])
                    t = Thread(target=self.cam_handler, name=name, args=(conn, addr, name))
                    t.start()
                elif name[0:3]=='STE': # 통신대상이 살균기일 경우
                    self.STElist.append(name)
                    self.STElist.sort(key=lambda x: x[4])
                    self.STECLEAN.append(False)
                    t = Thread(target=self.clean_handler, name=name, args=(conn, addr, name))
                    t.start()
            sock.close()

    def fininsh(self):
        #self.scheduler.shutdown()
        #self.conn.close()
        self.cursor.close()
        self.db.close()
        print('socket disconnect')