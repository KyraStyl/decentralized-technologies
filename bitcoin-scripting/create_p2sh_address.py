#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bitcoin Scripting -- Script 1

@author: Kyrama Styliani (AM: 76)

This script creates a P2SH Address from a given public (or optionally private) key

All funds sent to this address are locked for a specific time interval 
(either expressed in block height or Unix Epoch Time)
"""

from bitcoinutils.setup import setup
from bitcoinutils.transactions import Sequence, Locktime
from bitcoinutils.keys import P2shAddress, PrivateKey, PublicKey
from bitcoinutils.script import Script
from bitcoinutils.constants import TYPE_ABSOLUTE_TIMELOCK

import sys, getopt

man="""
This is a script to generate a P2SH Address
Obligatory parameters:
    -k, --key         Public Key (default - unless specified otherwise)
    -t, --time        Lock Time for the funds

Optional Parameters    
    -p, --private     Boolean Indicator whether the given key is private or not
    -o, --output      The name of the output file 
    
Example:
    create_p2sh_address.py -k PutHereThePK -t 20 -p true -o myp2shaddr.txt
"""

# =============================================================================
def saveToFile(filename, address):
    if ".txt" not in filename:
        filename += ".txt"
    with open(filename,"a") as f:
        f.write("\n")
        f.write(address)
    
def read_parameters(argv):
    try:
        opts, args = getopt.getopt(argv,"hk:t:p:o:",["key=","time=","private=","output="])
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
            elif opt in ("-p", "--private"):
                params["private"]=bool(arg)
            elif opt in ("-o", "--output"):
                params["output"]=arg
            
        if "key" not in params or "time" not in params:
            sys.exit(3)
        return params
    except:
        print("Read again the instructions carefully!")
        print(man)
        sys.exit(4)
    return

def create_p2sh_address(args):
    
    # define the sequence including the time interval the funds need to be locked
    #is_blocks = args["time"]<500000000 # may be unnecessary
    #seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, args["time"],is_blocks)
    seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, args["time"])
    
    if "private" in args:
        if args["private"] is True:
            # find the public key from the private key given
            p2pkh_sk = PrivateKey(args["key"])
            p2pkh_pk = p2pkh_sk.get_public_key()
    else:    
        # set the public key given
        p2pkh_pk = PublicKey(args["key"])
    
    
    # get the address (from the public key)
    p2pkh_addr = p2pkh_pk.get_address()
    
    # create the redeem script -- scriptPubKey -- locking script
    redeem_script = Script([seq.for_script(), 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP',
                            'OP_DUP', 'OP_HASH160', p2pkh_addr.to_hash160(),
                            'OP_EQUALVERIFY', 'OP_CHECKSIG'])
    
    # create a P2SH address from the above redeem script
    addr = P2shAddress.from_script(redeem_script)
    return addr.to_string()
    
def main():
    # set up the network
    setup('regtest')
    
    #read options and load to a dictionary
    options=read_parameters(sys.argv[1:]) 
    #print(options) -- just for debug
    
    # create the p2sh address using the relevant function
    p2sh_addr = create_p2sh_address(options)
    
    print("The corresponding P2SH Address is: ", p2sh_addr)
    
    if "output" in options:
        saveToFile(options["output"], p2sh_addr)


if __name__ == "__main__":
    main()
