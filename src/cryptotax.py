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

from os import system
import sys, getopt, requests, json, datetime, time, csv
import cryptotools as ct; 
from requests import api; 
config_file = "configuration.json"

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
    payments = ct.getPayments(config_obj)
    prices = ct.readPriceFile(config_obj)
    ct.generateCsvOutput(payments,prices,outputfile)

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

##Begin Main program
if __name__ == "__main__":
    main(sys.argv[1:]);
         
    
