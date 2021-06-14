from flask import Flask, render_template, request, jsonify
import pymysql


# 資料庫參數設定
db_settings = {
    "host": "127.0.0.1",
    "port": 8081,
    "user": "root",
    "password": "1234",
    "db": "schoolInfo",
    "charset": "utf8"
}

# 連線資料庫
try:
    # 建立Connection物件
    conn = pymysql.connect(**db_settings)
    # 建立Cursor物件
except Exception as ex:
    print(ex)


# 建立Flask物件app並初始化
app = Flask(__name__)

# 通過python裝飾器的方法定義路由地址


@app.route("/")
# 定義方法 用jinjia2引擎來渲染頁面，並返回一個index.html頁面
def root():
    return render_template("login.html")
# app的路由地址"/submit"即為ajax中定義的url地址，採用POST、GET方法均可提交




@app.route("/submit", methods=["POST"])
# 從這裡定義具體的函數 返回值均為json格式
def submit():
    # 由於POST、GET獲取資料的方式不同，需要使用if語句進行判斷
    if request.method == "POST":
        global studentId
        studentId = request.form.get("studentId")
        password = request.form.get("password")

    # 如果獲取的資料為空
    with conn.cursor() as cursor:
        # 測試看看有沒有抓到資料
        test = ''
        # 新增資料SQL語法
        command = "select * from student_info where student_id = " + studentId + " and password = '" + password + "'"
        # 我不知道要怎麼把post拿到的studemtId 跟 password帶進來!!!!!!!!!!!
        cursor.execute(command)
        test = cursor.fetchall()
        # 儲存變更
        conn.commit()
    
    # 列印抓到的資料
    if test == ():
        return {'message': "error!"}
    else:
        return {'message': "success!", 'studentId': studentId, 'password': password}

@app.route('/second')
def test():
    # 測試看看有沒有抓到資料
    test = ''
    with conn.cursor() as cursor:
        # 新增資料SQL語法
        command = "select * from student_info where student_id = " + studentId
        print(command)
        cursor.execute(command)
        test = cursor.fetchall()
        # 儲存變更
        conn.commit()
    # 列印抓到的資料
    print(test)
    test = str(test).replace("(", "")
    test = test.replace(")", "")
    test = test.replace("'", "")
    test = test.split(",")

    name = test[7]
    major = test[2]
    grade = test[8]
    status = test[3]
    double = test[5]
    minor = test[6]
    program = test[4]

    return render_template('second.html', name=name, major=major, grade=grade, status=status, double=double, minor=minor, program=program)



app.run(port=8080)
