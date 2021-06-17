#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bitcoin Scripting -- Script 2

@author: Kyrama Styliani (AM: 76)

This script spends all funds from a P2SH Address

More specifically:
- All funds from this address (the P2SH) are send to a P2PKH Address (given as a parameter)
- The Transaction created may contain more than one input transaction, but surely contains only one output
- All input transaction are signed seperately
- The fees are calculated using an estimation of fastestFees (from bitcoinfees.earn.com via api get request)
  based on the size of the transaction.
- Due to the fact that funds from P2SH Address (created by script 1) may be locked, 
  the validity of the transaction is being checked
- If the transaction is valid, it is send to the network, otherwise is cancelled.

- If there are no UTXOs available to spend of P2SH Address, then none of the above is executed, 
  and the program just ends with a simple message.
"""

from bitcoinutils.setup import setup
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, Sequence, Locktime
from bitcoinutils.keys import P2pkhAddress, P2shAddress, PrivateKey
from bitcoinutils.script import Script
from bitcoinutils.constants import TYPE_ABSOLUTE_TIMELOCK
from bitcoinutils.proxy import NodeProxy
from decimal import Decimal
import requests
import sys, getopt

man="""
This is a script to spend all UTXOs from a P2SH Address (and send them to a P2PKH Address)
Obligatory parameters:
    -k, --key          Private Key 
    -t, --time         Lock Time for the funds
    -s, --source       The P2SH Address (source of the funds)
    -d, --destination  The P2PKH Address (destination of the funds)

Optional Parameters 
    -u, --user        The user for NodeProxy
    -p, --pswd        The password for NodeProxy
    -o, --output      The name of the output file 
    
Example:
    spend_from_p2sh_address.py -k PrivKey -t 20 -s P2SHAddr -d P2PKHAddr -o spendinfo.txt
"""

def saveToFile(filename, messages):
    if ".txt" not in filename:
        filename += ".txt"
    with open(filename,"a") as f:
        for message in messages:
            f.write(message)
            f.write("\n")

def read_parameters(argv):
    try:
        opts, args = getopt.getopt(argv,"hk:t:s:d:u:p:o:",["key=","time=","source=","destination=","user=","pswd=","output="])
    except:
        print(man)
        sys.exit(1)
        
    try:
        params={}
        for opt,arg in opts:
            if opt == "-h":
                sys.exit(2)
            elif opt in ("-k", "--key"):
                params["key"]=arg
            elif opt in ("-t", "--time"):
                params["time"]=int(arg)
            elif opt in ("-s", "--source"):
                params["source"]=arg
            elif opt in ("-d", "--destination"):
                params["destination"]=arg
            elif opt in ("-u","--user"):
                params["user"]=arg
            elif opt in ("-p","--pswd"):
                params["pswd"]=arg
            elif opt in ("-o", "--output"):
                params["output"]=arg
            
        req = ["key","time","source","destination"]
        for arg in req:
            if arg not in params:
                sys.exit(3)
        if "user" not in params:
            params["user"]="user"
            params["pswd"]="password"
        return params
    except:
        print("Read again the instructions carefully!")
        print(man)
        sys.exit(4)
    return

def create_redeem_script(args):
    
    # define the sequence including the time interval the funds need to be locked
    #is_blocks = args["time"]<500000000 # may be unnecessary
    #seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, args["time"],is_blocks)
    seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, args["time"])
    
    # find the public key from the private key given
    p2pkh_sk = PrivateKey(args["key"])
    p2pkh_pk = p2pkh_sk.get_public_key()
    
    # get the address (from the public key)
    p2pkh_addr = p2pkh_pk.get_address()
    
    # create the redeem script
    redeem_script = Script([seq.for_script(), 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP',
                            'OP_DUP', 'OP_HASH160', p2pkh_addr.to_hash160(),
                            'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    return seq,redeem_script

def find_unspent_utxos(proxy, p2sh_addr, seq): 
    # import p2sh address to wallet just to "watch" it - like a "readOnly" address
    proxy.importaddress(p2sh_addr.to_string(), "address_to_watch", True)
    # find all unspent transactions - thus unspent UTXOs
    unspent_txs = proxy.listunspent(0, 99999999, [p2sh_addr.to_string()])
    
    total = 0 # calculate the total unspent UTXOs
    # create a list with all unspent transactions that will be used as input to the final transaction
    tx_list = [] 
    for tx in unspent_txs:
        total += tx['amount']
        tempTXin = TxInput(tx['txid'],tx['vout'],sequence=seq.for_input_sequence()) #input to the final transaction
        tx_list.append(tempTXin)
    return total, tx_list

def calc_fees(txin):
    fees = 0.01
    
    # make an http request to learn the fees in satoshis per byte 
    # to confirm the transaction as fast as possible
    jsonobj = requests.get("https://bitcoinfees.earn.com/api/v1/fees/recommended").json()
    fastestFees = jsonobj['fastestFee']
    
    # make an estimation about transaction total size 
    # using the formula: 180*in + 34*out + 10 + in
    total_size = 180*len(txin) + 34*1 + 10 + len(txin)
    
    fees = total_size*fastestFees / 10**8 #calculate the fees of the final transaction
    # print("\nFees == ",fees) -- just for debug
    return fees #in satoshis

def main():
    # set up the network
    setup('regtest')
    
    #read options and load to a dictionary
    options=read_parameters(sys.argv[1:]) 
    messages=[]
    
    seq,redeem_script = create_redeem_script(options)
    
    # -- unnecessary
    createdusingthescript = P2shAddress.from_script(redeem_script).to_string()
    
    message = "The P2SH Address created by the redeem script is : "+createdusingthescript
    messages.append(message)
    print(message)
    # unnecessary --
    
    # define locktime, used for the final transaction
    lock_time = Locktime(options["time"])
    
    # initialize the variable from arguments
    privkey = PrivateKey(options["key"])
    source_addr = P2shAddress(options["source"])
    dest_addr = P2pkhAddress(options["destination"])
    
    # get the public key from the private key given as an argument
    pubkey = privkey.get_public_key().to_hex()
    
    # establish connection to node proxy
    proxy = NodeProxy(options["user"],options["pswd"]).get_proxy()
    
    # find all unspent UTXOs from P2SH Address using the appropriate function
    total, tx_list = find_unspent_utxos(proxy, source_addr, seq)
    
    message = "The P2SH Address has in total "+str(len(tx_list))+" Transactions unspent"
    messages.append(message)
    print(message)
    
    # if there are available UTXOs to be spent
    if total>0:
        message = "Total bitcoins == "+str(total)
        messages.append(message)
        print(message)
        
        # calculate the fees based on the estimated size of the final transaction
        fees = calc_fees(tx_list)
        
        # create the output of the transaction (all funds are sent to the P2PKH Address, previously defined as destination)
        txout = TxOutput(to_satoshis(Decimal(total)-Decimal(fees)), dest_addr.to_script_pub_key())
        
        # create the final transaction
        tx = Transaction(tx_list,[txout],lock_time.for_transaction())
        
        # print raw unsigned transaction
        message = "Raw unsigned transaction: "+tx.serialize()
        messages.append(message)
        print(message)
        
        # Sign the transaction
        # for each tx input
        for index, txin in enumerate(tx_list):
            # create the signature and sign the tx input
            signature = privkey.sign_input(tx,index,redeem_script)
            
            # we have P2SH Address and thus scriptSig = unlocking script is defined as follows: 
            # unlocking script = (signature, public_key) (to unlock the p2pkh) + the redeem script (for p2sh)
            txin.script_sig = Script([signature, pubkey, redeem_script.to_hex()])
        
        
        signed_tx = tx.serialize()
        # print raw signed transaction ready to be broadcasted
        message="Raw signed transaction: " + signed_tx
        messages.append(message)
        print(message)
        
        # print transaction id
        message="Transaction Id - TxID: " + tx.get_txid()
        messages.append(message)
        print(message)
        
        # check validity of the created transaction
        is_valid = proxy.testmempoolaccept([signed_tx])
        
        # get the json response from the "testmempoolaccept" 
        message = "Transaction validity check result: " + str(is_valid)
        messages.append(message)
        print(message)
        
        # check if the transaction is valid and would be accepted from the network
        if is_valid[0]["allowed"]:
            # transaction is valid
            while True:
                send = input("\nBroadcast the transaction to the network? (y / n) : ")
                if send in ("y","Y"):
                    # broadcast the valid transaction to the network
                    sent_tx_id = proxy.sendrawtransaction(signed_tx)
                    message = "The transaction with id == "+sent_tx_id+", has been broadcasted to the network!"
                    messages.append(message)
                    print(message)
                    break
                if send in ("n","N"):
                    message = "Transaction's broadcast has been cancelled!"
                    messages.append(message)
                    print(message)
                    break
                print("\nInvalid input. Try again!")
                
        else:
            # transaction is invalid
            rejected = is_valid[0]["reject-reason"]
            message = "Unfortunately the signed raw transaction is invalid! Rejected because: "+rejected
            messages.append(message)
            print(message)
    else:
        # total == 0  => there are no utxos available to be spent
        message = "There are no UTXOs for this P2SH Address \nTry again with a different one!"
        messages.append(message)
        print(message)
    
    # if output file specified through parameters, save all the messages in this file
    if "output" in options:
        saveToFile(options["output"], messages)


if __name__ == "__main__":
    main()
