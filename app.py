from flask import Flask
import socketcom
from threading import Thread

app = Flask(__name__)

@app.route("/")
def print_hello():
    return 'test'

@app.route("/getSensor")
def get_sensor():
    #list = sc.get_CAMlist()
    #size = str(len(list))
    #sc.get_sensor()
    return "1"

@app.route("/clean")
def command_clean():
    #id = request.args.get('id',"error")
    #if id=="error":
    #    return "error"
    #sc.command_clean(id)
    return "success clean :"

@app.route("/document")
def get_document():
    #id = request.args.get('id', "error")
    #if id=="error":
    #    return "error"
    #sc.get_document()
    return "success"


if __name__ == "__main__":
    sc = socketcom.Socket()
    # 소켓통신 및 메인 스레드 실행
    t1=Thread(target=sc.run_server)
    t1.start()

    # 살균명령 스레드 실행 - 미완
    #t2=Thread(target=sc.commandClean)
    #t2.start()


    app.run(debug=False, host="0.0.0.0", port=5000)