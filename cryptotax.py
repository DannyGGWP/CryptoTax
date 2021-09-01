# Application to collate Crypto Payments and hystorical prices from an address. 
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

from io import UnsupportedOperation
from json.decoder import JSONDecodeError
from os import system
import sys, getopt, requests, json, datetime, time, csv

from requests import api; 
config_file = "configuration.json"
historical_prices = "prices.json"
help_msg = """
#############################################
This utility will pull recived transactions for an address and then pull the historical rates for the coin on the date of the txn and collate them into a CSV file for easy processing. \n
Currently supported Coins are Etherium, and this utility also supports The Eth Mainnet, and Polygon. 

Usage: 
        cryptotax.py -h             --help                                Display this message.
        cryptotax.py -g             --generate                            Generate a placeholder configuration.json.
        cryptotax.py -o <filename>  --output <filename>                   Specify the output file. 
        cryptotax.py -u             --update                              Interactivly set up the configuration file. (Not Working yet) 
#############################################
"""; 

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
        opts, args = getopt.getopt(argv, "hguo:",["output="]);
    except getopt.GetoptError:
        print("cryptotax.py -h"); 
        sys.exit(2); 
    for opt, arg in opts:
        
        if opt in ("-h","--help"):
            print(help_msg);
            sys.exit();  
        elif opt in ("-g","--generate"):
            print("Generating empty configuration.json");
            ## Generate code 
            generateConfigFile(); 
            print("Configuration file made. Please add your API Keys.")
            sys.exit(); 
        elif opt in ("-o","--output"):
            outputfile = arg; 
        else :
            print("Unrecognized flag.")
            sys.exit(2); 
    ## Load the Conf_object 
        config_obj = readConfFile; 
    ## Confirm the 
    if outputfile == "":
        print("No output file specified. Please spefiy an output file by running \n     cryptotax.py -o <output file name>");
        sys.exit(2); 
    print("Loading {conf_file} ...".format(conf_file = config_file)); 
    config_obj = readConfFile(); 
    print("Finished loading ...")
    payments = getPayments(config_obj)
    prices = readPriceFile(config_obj)
    generateCsvOutput(payments,prices,outputfile)

def generateConfigFile():
    config = {"miner" : {"addr" : "","pool_addr": "","coin": "eth","network": ""},"API" : {
        "polygonscan" : {"key" : "","url" : "https://api.polygonscan.com/api"},
        "etherscan" : {"key" : "","url" : "https://api.etherscan.io/api"},
        "alphavantage" : {"key" : "","url" : "https://www.alphavantage.co/query"}}}; 
    file = open(config_file,"w"); 
    json.dump(config.json(),file, indent= 6) 
    file.close();
## Read the conf file and return a conf object      
def readConfFile():
    try: 
        f = open(config_file); 
    except IOError: 
        print("Config File does not exist please generate one by running \n     cryptotax.py -g"); 
    return json.load(f); 
## Return an object of the recived transaction to the specified address 
def getPayments(config_obj):
    startBlk, endBlk = getTaxBlocks(config_obj); 
    network = config_obj["miner"]["network"]
    if network == "polygon":
        return getPolygonPayments(config_obj,startblk=startBlk,endblk=endBlk); 
    elif network == "eth":
        return getEthPayments(config_obj,startblk=startBlk,endblk=endBlk)

## Returns an object of token txs for WEATH (wrapped eth) sorted by ammount of WEATH then Filters baised on the sender address which should be you POOL 
def getPolygonPayments(config_obj,startblk = 0,endblk = 19999999):
    apiKey = config_obj["API"]["polygonscan"]["key"]
    addr = config_obj["miner"]["addr"]
    sender = config_obj["miner"].get("pool_addr","")
    payload = {"module" : "account", "action" : "tokentx", "address" : "{addr}".format(addr = addr), "startblock": "{start}".format(start = startblk), "endblock" : "{end}".format(end = endblk), "sort": "asc", "apikey" : "{apiKey}".format(apiKey = apiKey)}
    #print(payload)
    url = config_obj['API']["polygonscan"]["url"]
    response = requests.get(url,params=payload);
    #print(response.json()); 
    if response.json()["message"] != "OK":
        print("Response not ok. giving up");
        sys.exit(3); 
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

def getEthPayments(config_obj,startblk = 0,endblk = 19999999):
    apiKey = config_obj["API"]["etherscan"]["key"]
    addr = config_obj["miner"]["addr"]
    sender = config_obj["miner"].get("pool_addr","")
    payload = {"module" : "account", "action" : "txlist", "address" : "{addr}".format(addr = addr), "startblock": "{start}".format(start = startblk), "endblock" : "{end}".format(end = endblk), "sort": "asc", "apikey" : "{apiKey}".format(apiKey = apiKey)}
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

def getTaxBlocks(config_obj):
    network = config_obj["miner"]["network"]
    taxYear = config_obj["miner"].get("tax year","")
    api_key = ""
    api_url = ""
    if network == "polygon":
        api_key = config_obj["API"]["polygonscan"]["key"]
        api_url = config_obj["API"]["polygonscan"]["url"]
    elif network == "eth":
        api_key = config_obj["API"]["etherscan"]["key"]
        api_url = config_obj["API"]["etherscan"]["url"]
    jan1Taxyear = datetime.datetime(int(taxYear),1,1,0,0,0,0,tzinfo = datetime.timezone.utc )
    dec31Taxyear = datetime.datetime(int(taxYear),12,31,23,59,59,0, tzinfo = datetime.timezone.utc)
    now = datetime.datetime.now(tz = datetime.timezone.utc)
    ## If you are running this on the current year then dont use Dec 31st use Now instead 
    if now < dec31Taxyear: 
        dec31Taxyear = now; 
    beginPayload = {"module": "block", "action" : "getblocknobytime", "timestamp" : "{jan1}".format(jan1 = int(jan1Taxyear.timestamp())), "closest" : "after", "apikey" : "{apikey}".format(apikey = api_key)}; 
    endPayload = {"module": "block", "action" : "getblocknobytime", "timestamp" : "{dec31}".format(dec31 = int(dec31Taxyear.timestamp())), "closest" : "before", "apikey" : "{apikey}".format(apikey = api_key)};
    beginResponse = requests.get(api_url,params=beginPayload)
    #sleep to avoid rate limiting 
    time.sleep(0.2); 
    endresponse = requests.get(api_url,params=endPayload); 

    if beginResponse.json()["message"]  != "OK" or endresponse.json()['message'] != "OK":
        print("Response not ok. giving up");
        sys.exit(4);

    return (beginResponse.json().get("result",0), endresponse.json().get("result",19999999)) 

def generateCsvOutput(payments,prices,outputFile):
    with open(outputFile,'w',newline="") as csvfile:
        fieldNames = ['Date','Amount (eth)','Value (USD)']
        writer = csv.DictWriter(csvfile,fieldnames=fieldNames)
        writer.writeheader()
        for payment in payments:
            timestamp = payment['timeStamp'];
            amount = payment["value"]
            amountFlt = float(amount) * (10**-18.0)
            dt = datetime.datetime.fromtimestamp(float(timestamp))
            datestr = dt.date().strftime("%Y-%m-%d")
            value = getEthValue(datestr,amount,prices);
            writer.writerow({fieldNames[0] : "{date}".format(date=datestr),fieldNames[1] : "{amnt}".format(amnt=amountFlt), fieldNames[2] : "{value}".format(value=value)}) 

def getEthValue(datestr,amount,prices):
    #compare against the Low price for the day. 
    pricePerEth = prices["Time Series (Digital Currency Daily)"][datestr]["3a. low (USD)"]
    #devide amount by the decimal places of ETH which is 18 
    value = (float(amount)* (10**-18.0)) * float(pricePerEth)
    return value; 
def readPriceFile(config_obj):
    price_per = config_obj["miner"].get("price per", "day")
    api_function = ""
    api_key = config_obj["API"]["alphavantage"]["key"]
    if price_per == "day":
        api_function = "DIGITAL_CURRENCY_DAILY"
    elif price_per == "week":
        api_function = "DIGITAL_CURRENCY_WEEKLY"
    else:
        api_function = "DIGITAL_CURRENCY_MONTHLY"
    try: 
        f = open(historical_prices,"r+"); 
    except IOError: 
        print("Could not open price file. Quiting... "); 
        sys.exit(5); 

    try :
        price_dict = json.load(f); 
    except JSONDecodeError:
        price_dict = {"Meta Data": {"6. Last Refreshed": "1970-01-01 00:00:00"}}
    last_refreshed = datetime.datetime.strptime(price_dict.get("Meta Data","Meta Data").get("6. Last Refreshed","1970-01-01 00:00:00"),'%Y-%m-%d %H:%M:%S'); 
    today = datetime.datetime.now()
    print(last_refreshed)
    print(today)
    if last_refreshed.date() < today.date():
        print ("Historical data old... refreshing"); 
        payload = {"function" : "{func}".format(func = api_function), "symbol": "ETH", "market":"USD","apikey":"{apikey}".format(apikey = api_key)}
        prices_raw = requests.get(config_obj["API"]["alphavantage"]["url"],params=payload)
        price_dict = prices_raw.json()
        json.dump(prices_raw.json(),f, indent= 6)

    return price_dict 
##Begin Main program
if __name__ == "__main__":
    main(sys.argv[1:]);
         
    
