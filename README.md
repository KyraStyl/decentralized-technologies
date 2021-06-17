# decentralized-technologies

![Bitcoin-Rocket](https://media.giphy.com/media/trN9ht5RlE3Dcwavg2/giphy.gif)

This repository includes:

## 1. Bitcoin-scripting

### Script 1 - create_p2sh_address.py

This script creates a P2SH Address from a given public (or optionally private) key.
All funds sent to this address are locked for a specific time interval. 

To run this script:
```
python create_p2sh_address.py -k PutHereThePK -t PutTheTimeLockHere -p BooleanIndicator -o outputFile.txt
```

### Script 2 - spend_from_p2sh_address.py

This script spends all funds from a P2SH Address

To run this script:
```
python spend_from_p2sh_address.py -k PrivKey -t PutTheTimeLockHere -s P2SHAddr -d P2PKHAddr -o outputFile.txt
```

## 2. Ethereum-solidity

A smart contract that facilitates donations to different charities. 
