# -*- coding: utf-8 -*-
"""
@author: Giovanny Moncayo
"""
# =============================================================================
# DATA TRANSFORMATION SCRIPT
# Script to transform Google Location History (GLH) JSON files into CSV files
# Clone the code from Github 
# git@github.com:GmoncayoCodes/ActivityPointLocationGenerator.git
#
# Pre-requisites to run the script:
#   1. Check or create folders in your python directory: code, dataJSON
#   2. Copy scripts 01JSON-Transformation.py and 02APL-Processing.py in the code directory
#   3. Copy GLH JSON file in the dataJSON directory 
#   4. Set the folder code as your working directory
#   5. Run script
# =============================================================================

# Clean variables
from IPython import get_ipython
get_ipython().magic('reset -sf')

# =============================================================================
# PACKAGE IMPORTS
# =============================================================================
import pandas as pd

# =============================================================================
# UTILITY PACKAGE IMPORTS
# =============================================================================
import datetime as dt
import json, logging, os, platform, sys


try:
    # Get Working Directory
    urlWorkingDirectory = os.getcwd()
    if urlWorkingDirectory.endswith('code') :
        # Get Project Directory
        urlProjectDirectory = os.path.abspath(os.path.join(urlWorkingDirectory, os.pardir))
        msg = "Your working directory is: {}".format(urlWorkingDirectory)
        print(msg)
        # Create new directories in your python project folder
        newDirectories = ['dataTransform', 'dataFinal', 'log']
        flag = False
        for directory in newDirectories:
            try:
                pathDir = os.path.join(urlProjectDirectory, directory)
                if(not os.path.exists(pathDir)):
                    os.makedirs(pathDir)
                    flag = True
                else:
                    msg = "Directory '%s' already exists" % directory
                    print(msg) 
            except OSError as error:
                msg = "Directory '%s' can not be created" % directory
                print(msg)
                msg = "Error: {}".format(error)
                print(msg)            
        if(flag):
            msg = "New directories successfully created"
            print(msg)
        # Create URL access to new directories
        urlDataJSON = '{}\\{}'.format(urlProjectDirectory, 'dataJSON')
        urlDataTransform = '{}\\{}'.format(urlProjectDirectory, newDirectories[0])
        urlLog = '{}\\{}'.format(urlProjectDirectory, newDirectories[2])
        # Define log file
        now = str(dt.datetime.now()).replace(':', '')[0:17]
        logFile = 'log-Transformation'+ now +'.log'
        if platform.platform().startswith('Windows'):
            fichero_log = os.path.join(urlLog,logFile)
        else:
            fichero_log = os.path.join(os.getenv('HOME'), logFile)
        logging.basicConfig(level=logging.DEBUG, format ='%(asctime)s : %(levelname)s : %(message)s', 
                            filename = fichero_log, filemode = 'w',)
        
        msg = "*** START TRANSFORMATION STAGE ***"
        print(msg)
        logging.debug(msg)

        # =============================================================================
        # Algorithm to transform JSON files
        # =============================================================================

        try:
            # Validate dataJSON directory is not empty
            if(os.listdir(urlDataJSON)):
                # Reference first JSON file in dataJSON directory
                jsonFileName = os.listdir(urlDataJSON)[0]
                msg = "Processing File: {}".format(jsonFileName)
                print(msg)
                logging.info(msg)
                # Validate JSON file extension
                if(jsonFileName.endswith('.json')):
                    urlFile = '{}\\{}'.format(urlDataJSON, jsonFileName)
                    # Read JSON file
                    with open(urlFile, "r") as read_file:
                        dataFromJSON = json.load(read_file)
                    # Store JSON file data in a Dataframe
                    dataFrameSource = pd.DataFrame(dataFromJSON['locations'])
                    # Validate JSON file has data
                    if(not dataFrameSource.empty):
                        # Validate columns timestampMs, latitudeE7 and longitudeE7 exists in JSON structure
                        if(('timestampMs' in dataFrameSource.columns) and ('latitudeE7' in dataFrameSource.columns) and ('longitudeE7' in dataFrameSource.columns)):
                            # Select variables
                            dataFrameSource = dataFrameSource.loc[:, ['timestampMs', 'latitudeE7', 'longitudeE7']]
                            # Transform timestampMs to date format
                            dataFrameSource['datetime'] = pd.to_numeric(dataFrameSource['timestampMs'], errors='coerce')
                            dataFrameSource['datetime'] = dataFrameSource['datetime']/1000          
                            dataFrameSource['datetime'] = pd.to_datetime(dataFrameSource['datetime'], unit='s')
                            # Transform latitude and longitude to express in decimal degrees
                            dataFrameSource['latitude'] = dataFrameSource['latitudeE7']/1e7
                            dataFrameSource['longitude'] = dataFrameSource['longitudeE7']/1e7
                            # Final columns
                            dataFrameSource = dataFrameSource.loc[:, ['datetime', 'latitude', 'longitude']]
                            # Save data in CSV file
                            outputFileName = jsonFileName[0:len(jsonFileName)-5]
                            outputFileName = '{}.csv'.format(outputFileName)
                            urlSaveFile = '{}\\{}'.format(urlDataTransform,outputFileName)
                            dataFrameSource.to_csv(urlSaveFile, header=True, index = False)
                            msg = "*** File transformation succed!! ***"
                            print(msg)
                            logging.info(msg)
                            msg = "File output: {}".format(outputFileName)
                            print(msg)
                            logging.info(msg)
                            msg = "Number observations: {}".format(dataFrameSource.shape[0])
                            print(msg)
                            logging.info(msg)
                            startDate = dataFrameSource.iloc[0,0]
                            msg = "Data star date: {}".format(startDate)
                            print(msg)
                            logging.info(msg)
                            endDate = dataFrameSource.iloc[-1,0]
                            msg = "Data end date: {}".format(endDate)
                            print(msg)
                            logging.info(msg)
                            timePeriod = endDate -startDate
                            msg = "Total Time period: {}".format(timePeriod)
                            print(msg)
                            logging.info(msg)
                        else:
                            msg = 'No columns timestampMs, latitudeE7 or longitudeE7 in JSON File'
                            raise RuntimeError(msg)
                    else:
                        msg = 'Empty JSON file. Replace test.json in dataJSON directory'
                        raise RuntimeError(msg)
                else:
                    msg = 'Wrong JSON file extension ({})'.format(jsonFileName)
                    raise RuntimeError(msg)
            else:
                msg = 'No File to process. Check your dataJSON directory'
                raise FileNotFoundError(msg)   
            
            msg = "*** END TRANSFORMATION STAGE ***"
            print(msg)
            logging.debug(msg)
            logging.shutdown()  
            
            # Excecute processing stage
            exec(open("02AnLoCOV-Processing.py").read())
            
        except:
            msg = '{}: {}'.format(sys.exc_info()[0], sys.exc_info()[1])
            print(msg)
            logging.error(msg)
            logging.shutdown()
    else:
        msg = "Can't execute Script. Check your Working Directory is code directory!! Your current working directory is {}".format(urlWorkingDirectory)
        raise RuntimeError(msg)
except:
    msg = '{}: {}'.format(sys.exc_info()[0], sys.exc_info()[1])
    print(msg)
    logging.error(msg)
    logging.shutdown()