# Blockchain packages
import json
from web3 import Web3, HTTPProvider

# Flask API packages
import yaml
import pymysql
from flask_mysqldb import MySQL
from flask import Flask, render_template, request, jsonify, session

########################## Block chain Part ###########################

# create a web3.py instance w3 by connecting to the local Ethereum node
w3 = Web3(HTTPProvider("http://localhost:7545"))

# GLOBAL VARIABLE: compile your smart contract with truffle first
TRUFFLE_FILE = json.load(open('./build/contracts/Certificate.json'))
ABI = TRUFFLE_FILE['abi']
BYTECODE = TRUFFLE_FILE['bytecode']


def deploy_contract(school_key, student_key, student_name: str, school_name: str, major: str, minor: str, enroll_year: int):
    # Initialize a contract object with the smart contract compiled artifacts
    contract = w3.eth.contract(bytecode=BYTECODE, abi=ABI)

    # Initialize local account object from the private key of a valid Ethereum node address
    school_account = w3.eth.account.from_key(school_key)
    student_account = w3.eth.account.from_key(student_key)

    # build a transaction by invoking the buildTransaction() method from the smart contract constructor function
    construct_txn = contract.constructor(student_name, student_account.address, school_name, major, minor, enroll_year).buildTransaction({
        'from': school_account.address,
        'nonce': w3.eth.getTransactionCount(school_account.address),
    })

    # sign the deployment transaction with the private key
    signed = w3.eth.account.sign_transaction(construct_txn, school_account.key)

    # broadcast the signed transaction to your local network using sendRawTransaction() method and get the transaction hash
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    print(tx_hash.hex())

    # collect the Transaction Receipt with contract address when the transaction is mined on the network
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print("Contract Deployed At:", tx_receipt['contractAddress'])
    contract_address = tx_receipt['contractAddress']

    # Initialize a contract instance object using the contract address which can be used to invoke contract functions
    contract_instance = w3.eth.contract(abi=ABI, address=contract_address)
    return contract_address, contract_instance

#######################################################################


########################### Flask API Part ############################

app = Flask(__name__)

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


@app.route("/school/login/", methods=["GET", "POST"])
def student_login():
    if request.method == "GET":
        if check_school_login():
            school_id = session.get('school_id')  # 使用者姓名
            return render_template("school_index.html")
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
        if id_list:
            session["school_id"] = id_list[0]
            return redirect("/school/index/", code=302)
        else:
            data = {"err_msg": "帳號或密碼錯誤"}
            return render_template("school_index_not_login.html", data=data)


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
    app.run(debug=True, port=5000)
    # Initialize a local account object from the private key of a valid Ethereum node address
    school_account = w3.eth.account.from_key(
        "c79bac85d3f376fc47bd2455e288fee85290b71e9d6325da9268a3ed65b3eb0d")
    student_account = w3.eth.account.from_key(
        "560cff485cbab1ac6a66fcefa2d13cbd9ee915aabf733dc226a7423c5a09dcf3")
    # Deploy the smart contract
    deploy_contract(school_account, student_account,
                    "王小明", "國立政治大學", "資訊管理學系", "", 106)
