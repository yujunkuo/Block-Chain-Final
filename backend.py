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
    contract_address = address_list[0][0]
    return contract_address

# 透過學號取得姓名與地址
def get_name_and_address(student_id: str):
    cur = mysql.connection.cursor()
    command = "SELECT name, address FROM Student WHERE id = %s"
    cur.execute(command, (student_id, ))
    res_list = cur.fetchall()
    cur.close()
    name, address = res_list[0]
    return name, address

############################################################################

# 主頁 - 導向學生端與學校端
@app.route("/", methods=["GET"])
def homepage():
    return render_template("homepage.html")


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
@app.route("/student/index/", methods=["GET"])
def student_index():
    if not check_student_login():
        return redirect("/student/login/", code=302)
    data = {"student_id": session.get("student_id")}
    return render_template("student_index.html", data=data)
    

# 學生端 - 查看基本資料
@app.route("/student/info/", methods=["GET"])
def student_info():
    if not check_student_login():
        return redirect("/student/login/", code=302)
    student_id = session.get("student_id")
    contract_address = get_contract_address(student_id)
    student_name, student_address = get_name_and_address(student_id)
    data = {"student_id": student_id, "student_name": student_name, 
            "student_address": student_address, "contract_address": contract_address}
    return render_template("student_info.html", data=data)


# 學生端 - 查看修課紀錄
@app.route("/student/course/", methods=["GET"])
def student_course():
    if not check_student_login():
        return redirect("/student/login/", code=302)
    student_id = session.get("student_id")
    contract_address = get_contract_address(student_id)
    # 先找出該合約（學生）總共修過多少課程
    course_count = blockchain.get_course_count(contract_address)
    # 而後逐一取得其課程資訊
    course_info_list = list()
    for i in range(course_count):
        course_info = blockchain.get_course(contract_address, i)
        course_info_list.append(course_info)
    data = {"student_id": student_id, "course_info_list": course_info_list}
    return render_template("student_course.html", data=data)


# 學生端 - 檢查是否滿足畢業條件
@app.route("/student/certificate/", methods=["GET", "POST"])
def student_certificate():
    if not check_student_login():
        return redirect("/student/login/", code=302)
    if request.method == "GET":
        student_id = session.get("student_id")
        contract_address = get_contract_address(student_id)
        # 查看目前學籍狀態
        education_status = blockchain.get_education_status(contract_address)
        mapping_dict = {"undergraduate": "肄業", "learing": "在學中", "graduate": "已畢業"}
        education_status = mapping_dict[education_status]
        education_status_bool = False if education_status == "已畢業" else True
        # 檢查該學生是否滿足畢業條件
        check_finish = blockchain.check_finish_certificate(contract_address)
        if check_finish:
            data = {"student_id": student_id, "education_status": education_status,
                    "education_status_bool": education_status_bool,
                    "status": "已滿足畢業門檻", "status_bool": check_finish}
            return render_template("student_certificate.html", data=data)
        else:
            data = {"student_id": student_id, "education_status": education_status,
                    "education_status_bool": education_status_bool,
                    "status": "尚未滿足畢業門檻", "status_bool": check_finish}
            return render_template("student_certificate.html", data=data)
    elif request.method == "POST":
        try:
            student_id = session.get("student_id")
            student_key = request.form.get("student_key")
            contract_address = get_contract_address(student_id)
            # 修改學籍狀態（畢業）
            tx_hash = blockchain.set_certificate(student_key, contract_address)
            
            # 查看目前學籍狀態
            education_status = blockchain.get_education_status(contract_address)
            mapping_dict = {"undergraduate": "肄業",
                            "learing": "在學中", "graduate": "已畢業"}
            education_status = mapping_dict[education_status]
            education_status_bool = False if education_status == "已畢業" else True
            # 檢查該學生是否滿足畢業條件
            check_finish = blockchain.check_finish_certificate(
                contract_address)
            if check_finish:
                data = {"student_id": student_id, "education_status": education_status,
                        "education_status_bool": education_status_bool,
                        "status": "已滿足畢業門檻", "status_bool": check_finish}
            else:
                data = {"student_id": student_id, "education_status": education_status,
                        "education_status_bool": education_status_bool,
                        "status": "尚未滿足畢業門檻", "status_bool": check_finish}
            if tx_hash:
                data["suc_msg"] = "修改成功! 恭喜畢業!"
                data["tx_hash"] = "Hash: " + tx_hash
                return render_template("student_certificate.html", data=data)
            else:
                data["err_msg"] = "修改失敗!"
                return render_template("student_certificate.html", data=data)
        except:
            data["err_msg"] = "修改失敗!"
            return render_template("student_certificate.html", data=data)
        
        
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
@app.route("/school/index/", methods=["GET"])
def school_index():
    if not check_school_login():
        return redirect("/school/login/", code=302)
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
    elif request.method == "POST":
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
    elif request.method == "POST":
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
            # 上傳課程紀錄
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
    if not check_school_login():
        return redirect("/school/login/", code=302)
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

# Main
if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.run(debug=True, port=5000)
