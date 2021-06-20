# Flask API packages
import yaml
import pymysql
from flask_mysqldb import MySQL
from flask import Flask, render_template, request, jsonify, session, redirect
from blockchain import Blockchain


app = Flask(__name__)

blockchain = Blockchain()


# Read MySQL Config
with open("./config/database.yml", 'r') as stream:
    try:
        mysql_config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# Set MySQL Config
app.config["MYSQL_HOST"] = mysql_config["host"]
app.config["MYSQL_USER"] = mysql_config["username"]
app.config["MYSQL_PASSWORD"] = mysql_config["password"]
app.config["MYSQL_DB"] = mysql_config["database"]

# Construct MySQL Object
mysql = MySQL(app)


# 確認學校使用者是否登入
def check_school_login():
    return session.get('school_id')

# 確認學生使用者是否登入
def check_student_login():
    return session.get('student_id')

# 取得學校的 name
def get_school_name(school_id: str):
    cur = mysql.connection.cursor()
    command = "SELECT name FROM School WHERE id = %s"
    cur.execute(command, (school_id, ))
    id_list = cur.fetchall()
    cur.close()
    name = id_list[0][0]
    return name

# 將合約地址儲存於學生的 table 內
def store_contract_address(student_address: str, contract_address: str):
    try:
        cur = mysql.connection.cursor()
        command = "UPDATE Student SET contract_address = %s WHERE address = %s"
        cur.execute(command, (contract_address, student_address))
        mysql.connection.commit()
        cur.close()
        return True
    except:
        return False

# 透過學號取得合約地址
def get_contract_address(student_id: str):
    cur = mysql.connection.cursor()
    command = "SELECT contract_address FROM Student WHERE id = %s"
    cur.execute(command, (student_id, ))
    address_list = cur.fetchall()
    cur.close()
    address = address_list[0][0]
    return address

############################################################################

# 學生端 - 登入
@app.route("/student/login/", methods=["GET", "POST"])
def student_login():
    if request.method == "GET":
        if check_student_login():
            student_id = session.get('student_id')  # 使用者姓名
            return redirect("/student/index/")
        else:
            data = {}
            return render_template("student_index_not_login.html", data=data)
    elif request.method == "POST":
        student_id = request.form.get("student_id")
        password = request.form.get("password")
        cur = mysql.connection.cursor()
        command = "SELECT id FROM Student WHERE id = %s AND password = %s"
        cur.execute(command, (student_id, password))
        id_list = cur.fetchall()
        cur.close()
        if id_list:
            session["student_id"] = id_list[0][0]
            return redirect("/student/index/")
        else:
            data = {"err_msg": "帳號或密碼錯誤"}
            return render_template("student_index_not_login.html", data=data)


# 學生端 - 首頁
@app.route("/student/index/", methods=["GET", "POST"])
def student_index():
    if not check_student_login():
        return redirect("/student/login/", code=302)
    if request.method == "GET":
        data = {"student_id": session.get("student_id")}
        return render_template("student_index.html", data=data)


# 學生端 - 登出
@app.route("/student/logout/", methods=["GET", "POST"])
def student_logout():
    session["student_id"] = False
    return redirect("/student/index/")

############################################################################
############################################################################

# 學校端 - 登入
@app.route("/school/login/", methods=["GET", "POST"])
def school_login():
    if request.method == "GET":
        if check_school_login():
            school_id = session.get('school_id')  # 使用者姓名
            return redirect("/school/index/")
        else:
            data = {}
            return render_template("school_index_not_login.html", data=data)
    elif request.method == "POST":
        school_id = request.form.get("school_id")
        password = request.form.get("password")
        cur = mysql.connection.cursor()
        command = "SELECT id FROM School WHERE id = %s AND password = %s"
        cur.execute(command, (school_id, password))
        id_list = cur.fetchall()
        cur.close()
        if id_list:
            session["school_id"] = id_list[0][0]
            return redirect("/school/index/")
        else:
            data = {"err_msg": "帳號或密碼錯誤"}
            return render_template("school_index_not_login.html", data=data)


# 學校端 - 首頁
@app.route("/school/index/", methods=["GET", "POST"])
def school_index():
    if not check_school_login():
        return redirect("/school/login/", code=302)
    if request.method == "GET":
        data = {"school_id": session.get("school_id")}
        return render_template("school_index.html", data=data)


# 學校端 - 發起新合約
@app.route("/school/new/", methods=["GET", "POST"])
def school_new():
    if not check_school_login():
        return redirect("/school/login/", code=302)
    if request.method == "GET":
        data = {"school_id": session.get("school_id")}
        return render_template("school_new.html", data=data)
    if request.method == "POST":
        try:
            school_id = session.get("school_id")
            school_key = request.form.get("school_private_key")
            school_name = get_school_name(school_id)
            student_address = request.form.get("student_address")
            student_name = request.form.get("student_name")
            major = request.form.get("major")
            minor = request.form.get("minor")
            enroll_year = int(request.form.get("enroll_year"))
            # 部署合約
            contract_address, contract_instance = blockchain.deploy_contract(
                school_key, student_address, student_name, school_name, major, minor, enroll_year)
            # 將合約地址寫入資料庫的 Student Table
            res_status = store_contract_address(
                student_address, contract_address)
            if res_status:
                data = {"school_id": school_id,
                        "suc_msg": "部署合約成功!",
                        "contract_address": "合約地址: " + str(contract_address),
                        }
                return render_template("school_new.html", data=data)
            else:
                data = {"school_id": school_id,
                        "err_msg": "儲存合約地址失敗!",
                        }
                return render_template("school_new.html", data=data)
        except:
            data = {"school_id": school_id,
                    "err_msg": "部署合約失敗!",
                    }
            return render_template("school_new.html", data=data)


# 學校端 - 上傳課程紀錄
@app.route("/school/upload/", methods=["GET", "POST"])
def school_upload():
    if not check_school_login():
        return redirect("/school/login/", code=302)
    if request.method == "GET":
        data = {"school_id": session.get("school_id")}
        return render_template("school_upload.html", data=data)
    if request.method == "POST":
        try:
            school_id = session.get("school_id")
            school_key = request.form.get("school_private_key")
            school_name = get_school_name(school_id)
            student_id = request.form.get("student_id")
            course_name = request.form.get("course_name")
            course_content = request.form.get("course_content")
            course_comment = request.form.get("course_comment")
            course_grade = int(request.form.get("course_grade"))
            contract_address = get_contract_address(student_id)
            # 部署合約
            tx_hash = blockchain.set_course(
                school_key, contract_address, course_name, course_content, course_comment, course_grade)
            if tx_hash:
                data = {"school_id": school_id,
                        "suc_msg": "上傳成功!",
                        "tx_hash": "Hash: " + tx_hash,
                        }
                return render_template("school_upload.html", data=data)
            else:
                data = {"school_id": school_id,
                        "err_msg": "上傳失敗!",
                        }
                return render_template("school_upload.html", data=data)
        except:
            data = {"school_id": school_id,
                    "err_msg": "上傳失敗!",
                    }
            return render_template("school_upload.html", data=data)


# 學校端 - 查看學生資訊
@app.route("/school/view/", methods=["GET"])
def school_view():
    cur = mysql.connection.cursor()
    command = "SELECT id, name, address, contract_address FROM Student"
    cur.execute(command)
    student_list = cur.fetchall()
    cur.close()
    data = {"school_id": session.get(
        "school_id"), "student_list": student_list}
    return render_template("school_view.html", data=data)


# 學校端 - 登出
@app.route("/school/logout/", methods=["GET", "POST"])
def school_logout():
    session["school_id"] = False
    return redirect("/school/index/")

############################################################################

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


#######################################################################
# Main
if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.run(debug=True, port=5000)
    # Initialize a local account object from the private key of a valid Ethereum node address
    school_account = w3.eth.account.from_key(
        "c79bac85d3f376fc47bd2455e288fee85290b71e9d6325da9268a3ed65b3eb0d")
    student_account = w3.eth.account.from_key(
        "560cff485cbab1ac6a66fcefa2d13cbd9ee915aabf733dc226a7423c5a09dcf3")
    # Deploy the smart contract
    deploy_contract(school_account, student_account,
                    "王小明", "國立政治大學", "資訊管理學系", "", 106)
