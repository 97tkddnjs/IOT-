import socket
from flask import Flask
from flask import jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import sys
from datetime import datetime
import apscheduler.schedulers.blocking
import time
import socketcom
from threading import Thread
#from pynput import keyboard

app = Flask(__name__)

@app.route("/")
def print_hello():
    return 'test'


@app.route("/info", methods=["POST"])
def info():
    info_dict = dict()
    info_dict["IP_ADDRESS"] = socket.gethostbyname(socket.gethostname())
    info_dict["HOST_NAME"] = socket.gethostname()
    return info_dict

def loop():
    while True:
        print(111)
        time.sleep(3)

# def keyboardInterrupt():
#     with keyboard.Listener(
#             on_press=on_press) as listener:
#         listener.join()

# def on_press(key):
#     try:
#         print('Alphanumeric key pressed: {0} '.format(
#             key.char))
#     except AttributeError:
#         print('special key pressed: {0}'.format(
#             key))



if __name__ == "__main__":
    sc = socketcom.Socket()
    # 소켓통신 및 메인 스레드 실행
    t1=Thread(target=sc.run_server)
    t1.start()

    # 살균명령 스레드 실행 - 미완
    t2=Thread(target=sc.commandClean)
    t2.start()

    # 스레드 테스트 루프 실행
    t3 = Thread(target=loop)
    t3.start()

    # # 키보드 입력 스레드 실행 - 미완
    # t4=Thread(target=keyboardInterrupt)
    # t4.start()
    # app.run(debug=False, host="0.0.0.0", port=5000)