# Application to coalate Crypto Payments and hystorical prices from an address. 
#Copyright (C) 2021  Daniel Guerrera
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys, getopt, requests, json

from requests import api; 
config_file = "configuration.json"


def main(argv):
    addr = ""; 
    coin = ""; 
    network = ""; 
    year = ""
    sender = ""; 
    save = False; 
    outputfile = ""; 
    config_obj = {};
    try: 
        opts, args = getopt.getopt(argv, "hguo:a:c:n:s:y:",["output=","addr=","coin=","network=","sender=","year="]);
    except getopt.GetoptError:
        print("cryptotax.py -h"); 
        sys.exit(2); 
    for opt, arg in opts:
        
        if opt == "-h":
            help_msg = "This utility will pull recived transactions for an address and then pull the historical rates for the coin on the date of the txn and coalate them into a CSV file for easy processing. \n" \
            "Currently supported Coins are Etherium, and this utility also supports The Eth Mainnet, Polygon"
            print(help_msg); 
        elif opt == "-g":
            print("Generating empty configuration.json");
            ## Generate code 
            generateConfigFile(); 
            print("Configuration file made. Please add your API Keys.")
        elif opt in ("-o","--output"):
            outputfile = arg; 
        else :
            print("Unrecognized flag.")
            sys.exit(2); 
    ## Load the Conf_object 
        config_obj = readConfFile; 
    ## Confirm the 

    print("Reading miner data from configuration file..."); 
    config_obj = readConfFile(); 
    print (config_obj); 
    #print(config_obj["API"]["polygonscan"]["key"]); 
    print(getPolygonPayments(config_obj["miner"]["addr"],config_obj["miner"]["pool_addr"],config_obj["miner"]["coin"],config_obj["miner"]["tax year"],config_obj));

def generateConfigFile():
    config = {"miner" : {"addr" : "","pool_addr": "","coin": "eth","network": ""},"API" : {"polygonscan" : {"key" : "","url" : "https://api.polygonscan.com/api"},"etherscan" : {"key" : "","url" : "https://api.etherscan.io/api"}}}; 
    config_JSON = json.dump(config); 
    file = open(config_file,"w"); 
    file.write(config_JSON); 
    file.close();
## Read the conf file and return a conf object      
def readConfFile():
    try: 
        f = open(config_file); 
    except IOError: 
        print("Config File does not exist please generate one by running cryptotax.py -g"); 
    return json.load(f); 
## Return an object of the recived transaction to the speccified address 
def getPayments(addr,sender,network, coin, year,config_obj):
    if network == "polygon":
        getPolygonPayments(addr,sender,config_obj); 
    elif network == "eth":
        getEthPayments(addr,sender,config_obj)
## Returns an object of token txs for WEATH (wrapped eth) sorted by ammount of WEATH then Filters baised on the sender address which should be you POOL 
def getPolygonPayments(addr,sender,coin,year,config_obj):
    apiKey = config_obj["API"]["polygonscan"]["key"]
    payload = {"module" : "account", "action" : "tokentx", "address" : "{addr}".format(addr = addr), "startblock": "0", "endblock" : "19999999", "sort": "asc", "apikey" : "{apiKey}".format(apiKey = apiKey)}
    #print(payload)
    url = config_obj['API']["polygonscan"]["url"]
    response = requests.get(url,params=payload);
    print(response.url);
    #print(response.json()); 
    if response.json()["message"] != "OK":
        print("Response not ok. giving up");
        sys.exit(2); 
    results = response.json()["result"]; 
    payments = [];
    ## If no sender specified then do not filter results on the sender instead filter on the Reciver (the miner address)
    if sender == "":
        for result in results:
            if result["to"] == addr:
                payments.append(result)
        return payments; 
    ## scan for txs from the pool address
    for result in results:
        if result["from"] == sender:
            payments.append(result); 
    return payments; 

def getEthPayments(addr,sender,config_obj):
    apiKey = config_obj["API"]["etherscan"]["key"]
    payload = {"module" : "account", "action" : "txlist", "address" : "{addr}".format(addr = addr), "startblock": "0", "endblock" : "19999999", "sort": "asc", "apikey" : "{apiKey}".format(apiKey = apiKey)}
    #print(payload)
    url = config_obj['API']["etherscan"]["url"]
    response = requests.get(url,params=payload);
    if response.json()["message"] != "OK":
        print("Response not ok. giving up");
        sys.exit(2); 
    results = response.json()["result"]; 
    payments = [];
    ## If no sender specified then do not filter results on the sender instead filter on the Reciver (the miner address)
    if sender == "":
        for result in results:
            if result["to"] == addr:
                payments.append(result)
        return payments; 
    ## scan for txs from the pool address
    for result in results:
        if result["from"] == sender:
            payments.append(result); 
    return payments; 
if __name__ == "__main__":
    main(sys.argv[1:]);
         
    
