import json
from web3 import Web3
from solc import compile_files, link_code

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

contracts = compile_files(['smart_contract.sol'])

main_contract = contracts.pop("smart_contract.sol:Certificate")

def deploy_contract(contract_interface):
    # 部署合約
    contract = w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
            )
    # 獲取交易哈希
    tx_hash = contract.deploy(
            transaction={'from': w3.eth.accounts[1]}
            )
    # 獲取 tx 收據以獲取合約地址
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    return tx_receipt['contractAddress']

def main():
    contract_address = deploy_contract(main_contract)

    with open('data.json', 'w') as outfile:
        data = {
                "abi": main_contract['abi'],
                "contract_address": contract_address,
               }
        json.dump(data, outfile, indent=4, sort_keys=True)

if __name__ == "__main__":
    main()

