# Blockchain packages
import json
from web3 import Web3, HTTPProvider


class Blockchain:

    # 初始化 - 建立 w3 物件、智能合約檔案導入、取得 ABI 與 Bytecode 內容
    def __init__(self):
        # create a web3.py instance w3 by connecting to the local Ethereum node
        self.w3 = Web3(HTTPProvider("http://localhost:7545"))

        # GLOBAL VARIABLE: compile your smart contract with truffle first
        self.TRUFFLE_FILE = json.load(
            open('./build/contracts/Certificate.json'))
        self.ABI = self.TRUFFLE_FILE['abi']
        self.BYTECODE = self.TRUFFLE_FILE['bytecode']

    # 部署合約
    def deploy_contract(self, school_key, student_address, student_name: str, school_name: str, major: str, minor: str, enroll_year: int):
        # Initialize a contract object with the smart contract compiled artifacts
        contract = self.w3.eth.contract(bytecode=self.BYTECODE, abi=self.ABI)

        # Initialize local account object from the private key of a valid Ethereum node address
        school_account = self.w3.eth.account.from_key(school_key)

        # build a transaction by invoking the buildTransaction() method from the smart contract constructor function
        construct_txn = contract.constructor(student_name, student_address, school_name, major, minor, enroll_year).buildTransaction({
            'from': school_account.address,
            'nonce': self.w3.eth.getTransactionCount(school_account.address),
        })

        # sign the deployment transaction with the private key
        signed = self.w3.eth.account.sign_transaction(
            construct_txn, school_account.key)

        # broadcast the signed transaction to your local network using sendRawTransaction() method and get the transaction hash
        tx_hash = self.w3.eth.sendRawTransaction(signed.rawTransaction)
        print(tx_hash.hex())

        # collect the Transaction Receipt with contract address when the transaction is mined on the network
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        print("Contract Deployed At:", tx_receipt['contractAddress'])
        contract_address = tx_receipt['contractAddress']

        # Initialize a contract instance object using the contract address which can be used to invoke contract functions
        contract_instance = self.w3.eth.contract(
            abi=self.ABI, address=contract_address)
        return contract_address, contract_instance

    # 上傳課程紀錄
    def set_course(self, school_key: str, contract_address: str, name: str, content: str, comment: str, grade: int):
        contract_instance = self.w3.eth.contract(
            abi=self.ABI, address=contract_address)
        school_account = self.w3.eth.account.from_key(school_key)
        construct_txn = contract_instance.functions.setCourse(name, content, comment, grade).buildTransaction({
            'from': school_account.address,
            'nonce': self.w3.eth.getTransactionCount(school_account.address),
        })
        signed = self.w3.eth.account.sign_transaction(
            construct_txn, school_account.key)
        tx_hash = self.w3.eth.sendRawTransaction(signed.rawTransaction)
        return tx_hash.hex()
