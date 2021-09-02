
from io import UnsupportedOperation
from json.decoder import JSONDecodeError
import os
import sys, requests, json, datetime, time, csv
historical_prices = "prices.json"
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
    url = config_obj['API']["polygonscan"]["url"]
    response = requests.get(url,params=payload);
    if response.json()["message"] != "OK":
        print("Response not ok. giving up");
        sys.exit(3); 
    results = response.json()["result"]; 
    return filterPayments(addr,sender,results); 
    
def filterPayments(addr,sender,results):
    payments = [];
    ## If no sender specified then do not filter results on the sender instead filter on the Reciver (the miner address)
    if sender == "":
        print("No Pool Address specified. Grabing all incoming TXS")
        for result in results:
            if result["to"] == addr:
                payments.append(result)
        return payments; 
    ## scan for txs from the pool address
    for result in results:
        if result["from"] == sender:
            payments.append(result); 
    if payments == []:
        print("No transactions found. Check config file an insure Eth Address and Pool address are correct. ")
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
    return filterPayments(addr,sender,results); 

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
    if last_refreshed.date() < today.date():
        f.close()
        f = open(historical_prices,"w")
        print ("Historical data old... refreshing"); 
        
        payload = {"function" : "{func}".format(func = api_function), "symbol": "ETH", "market":"USD","apikey":"{apikey}".format(apikey = api_key)}
        prices_raw = requests.get(config_obj["API"]["alphavantage"]["url"],params=payload)
        price_dict = prices_raw.json()
        json.dump(prices_raw.json(),f, indent= 6)

    return price_dict 