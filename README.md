# CryptoTax
Small python application to Coalate Crypto payments and historical rates for tax reporting. 
Written with small time Etherium miners in mind, this application can pull payments to a Miner's Wallet address and even filter by pool address. 
It can then pull historical rates for etherium on the Day, Week, or Month, of the payout and will generate a CSV file for further processing in Excel or Sheets. 

## How to use. 
This is a command line script and you will need python 3.9 to run it. Start by making your configuration.json file. you can generate a basic configuration file using the command `$cryptotax.py -g` or `$cryptotax.py --generate`. Once the base file is made you will need to fill in some important details. 
### Miner settings
This setting is for your information. Lets go over the options. 
- Your address (addr): manditory, the wallet address you want to inspect for incoming transactions. 
- Pool Address (pool_addr): optional, but recomended. Thit will filter incoming incoming transactions by a specific address. Usually you'll want this to be your pools address  
- Coin (coin): manditory currently this only supports eth, and wrapped eth on the polygon chain so leave it as eth. 
- Network (network): manditory, the network you payout on currently Mainnet (eth) and Polygon (polygon) are supported
- Tax Year (tax year), optional, the tax year you'd like to filter on. This will limit transactions pulled between the first block of the tax year, Jan 1 00:00:00 and the last block of the tax year Dec 31 23:59:59 OR the most recent validated block if Dec 31st is in the future. NOTE: this can be a bit broken for polygon as their first block according to polygonscan was in early 2020 which means a block for any year before 2020 does not exist and will fail the API query. 
- Price per (price per): optional but defaults to day, tell the program how you would like to build the historical prices file. Currently only daily has been supported and tested. 
An example miner settings is provided below 
```
"miner" : {
    "addr" : "<Your Wallet address>",
    "pool_addr": "<Pool address>",
    "coin": "eth", 
    "network": {"eth" | "polygon"},
    "tax year": "2021",
    "price per": "day" 
}
```

### API settings. 
This tool relies on 3 APIs to work its magic. Offline support might be added in the future but for now you must rely on them. You will need to generate an API Key for each of the API's.  The APIs are: 
- [Etherscan.io](https://etherscan.io/) For Etherium Mainnet  
- [Polygonscan.com](https://polygonscan.com/) For the Polygon sidechain
- [Alphavantage](https://www.alphavantage.co/) For historical coin prices 
Follow instructions on their sites to generate API keys and paste them into the approprite sections of the configuration.json file. I cannot provide keys as that would require me to pay for them and as this tool is free and opensource paying for that is outside of my budget. 
Alphavantage will only need to be quried at most once per day as it will save the historical prices to a prices.json file to avoid excessive calls to that API. 
```
"API" : {
        "polygonscan" : {
            "key" : "YOUR API KEY",
            "url" : "https://api.polygonscan.com/api"
        },
        "etherscan" : {
            "key" : "YOUR API KEY",
            "url" : "https://api.etherscan.io/api"

        },
        "alphavantage" : {
            "key" : "YOUR API KEY",
            "url" : "https://www.alphavantage.co/query"
        }
    }
```