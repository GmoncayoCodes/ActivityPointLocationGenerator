# Script to transform Google Location History (GLH) JSON files in RData files
# Pre-requisites to run Script --------------------------------------------
# Copy JSON file sent by Google in dataJSON directory

# Package installation (If necessary)------------------------------------
#install.packages('jsonlite')
#install.packages('dplyr')
#install.packages('lubridate')
#install.packages('stringr')
#install.packages('rlang')

# library imports ---------------------------------------------------------
library(jsonlite)
library(dplyr)
library(lubridate)
library(stringr)
library(rlang)

# Get working directory of your R Project
urlWorkingDirectory = getwd()
setwd(urlWorkingDirectory)
print(paste('Your working directory is:',urlWorkingDirectory))

# Create new directories --------------------------------------------------
newDirectories<-c('dataTransform', 'dataFinal', 'log')
for (i in seq_along(newDirectories) ) {
  dir.create(file.path(newDirectories[i])) 
}  

# Create URL access to directories
urlDataJSON = paste(urlWorkingDirectory,'/dataJSON/',sep = '')
urlDataTransform = paste(urlWorkingDirectory,'/',newDirectories[1],'/',sep = '')
urlLog = paste(urlWorkingDirectory,'/',newDirectories[3],'/',sep = '')

# Algorithm to decrypt JSON file ------------------------------------------

tryCatch(
  {
    # Define Log File for the process
    logFile = paste(urlLog,"log-Transformation",trimws(str_replace_all(as.character(Sys.time()),":","")),".txt")
    con <- file(logFile, open="a")
    textMessage = paste('Process start Time: ',as.character(Sys.time()))
    print(textMessage)
    writeLines(textMessage, con = con)
    
    # Set working directory to dataJSON directory
    setwd(urlDataJSON)
    # validate Only one JSON file exists
    if(length(list.files(pattern = '\\.json$')) == 1){
      # File name
      jsonFileName = list.files(pattern = '\\.json$')
      # Validate JSON file extension
      if(endsWith(jsonFileName, '.json')){
        # Read JSON file
        dataFromJSON <- fromJSON(file.path(urlDataJSON, jsonFileName))
        # Store data in a Dataframe
        dataFrameSource <- dataFromJSON$locations
        # Validate dataframe has data
        if(!is_empty(dataFrameSource)){
          #Validate dataframe has at least 3 columns
          if(ncol(dataFrameSource)>=3){
            # Validate columns timestampMs, latitudeE7 and longitudeE7 exists
            if(length(str_subset(colnames(dataFrameSource), 'timestampMs'))==1 & 
               length(str_subset(colnames(dataFrameSource), 'latitudeE7'))==1 &
               length(str_subset(colnames(dataFrameSource), 'longitudeE7'))==1){
              # Select variables
              dataFrameSource = dataFrameSource %>%
                select(timestampMs, latitudeE7, longitudeE7)
              # Transform timestampMs to date format
              dataFrameSource$timestampMs <- as.POSIXct(as.numeric(dataFrameSource$timestampMs)/1000, origin='1970-01-01')
              # Location (Divide by 1e7 to express in decimal degrees)
              dataFrameSource$latitudeE7 <-dataFrameSource$latitudeE7/1e7  #1e7 = 10000000 X-coordinate
              dataFrameSource$longitudeE7 <- dataFrameSource$longitudeE7/1e7 #1e7 = 10000000 Y-coordinate
              # Save RData file
              rdataFileName = paste(substr(jsonFileName, 1, nchar(jsonFileName)-5),'.RData',sep='')
              urlSaveFileRdata = paste(urlDataTransform,rdataFileName,sep='')
              save(dataFrameSource, file=urlSaveFileRdata)
              textMessage = 'File decryption succed!!'
              print(textMessage)
              writeLines(textMessage, con = con)
              textMessage = '***** Summary *****'
              print(textMessage)
              writeLines(textMessage, con = con)
              textMessage = paste('File name: ', jsonFileName)
              print(textMessage)
              writeLines(textMessage, con = con)
              textMessage = paste('File observations: ', nrow(dataFrameSource))
              print(textMessage)
              writeLines(textMessage, con = con)
              startDate = dataFrameSource[1,1]
              textMessage = paste('Star date of data: ', startDate)
              print(textMessage)
              writeLines(textMessage, con = con)
              endDate = dataFrameSource[nrow(dataFrameSource), 1]
              textMessage = paste('End date of data: ', endDate)
              print(textMessage)
              writeLines(textMessage, con = con)
              timePeriod = endDate -startDate
              textMessage = paste('Time period: ', as.period(timePeriod))
              print(textMessage)
              writeLines(textMessage, con = con)
              textMessage = paste('Total time: ',as.duration(timePeriod))
              print(textMessage)
              writeLines(textMessage, con = con)
            }else{
              textMessage = 'File estructure exception: No columns timestampMs, latitudeE7 or longitudeE7 in JSON File'
              print(textMessage)
              writeLines(textMessage, con = con)
            } 
          }else{
            textMessage = 'File estructure exception: File has less than three columns'
            print(textMessage)
            writeLines(textMessage, con = con)
          }
        }else{
          textMessage = 'Dataframe exception: No data in JSON file'
          print(textMessage)
          writeLines(textMessage, con = con)
        }
      }else{
        textMessage = 'File format exception: Wrong JSON file extension'
        print(textMessage)
        writeLines(textMessage, con = con)
      }
    }else{
      textMessage = 'File exception: More than one JSON file or NO JSON file in dataJSON directory'
      print(textMessage)
      writeLines(textMessage, con = con)
    }
    # Set Default working directory
    setwd(urlWorkingDirectory)
    textMessage = paste('Process end Time: ', as.character(Sys.time()))
    print(textMessage)
    writeLines(textMessage, con = con)
    close(con)
  },warning = function(w) {
    textMessage = paste('WARNING MESSAGE: ',w)
    print(textMessage)
    writeLines(textMessage, con = con)
    close(con)
  },error = function(e) {
    setwd(urlWorkingDirectory)
    textMessage = paste('ERROR MESSAGE: ',e)
    print(textMessage)
    writeLines(textMessage, con = con)
    close(con)
  }
)