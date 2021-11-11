# Welcome to Activity Point Location (APL) Project

GPS data collection using mobile devices is of particular interest. This data provides detailed information on people's daily movements due to devices' ubiquity and daily use. 

This project contain scripts to compute Activity Point Location (APL) from mobile devices' GPS tracking. We use Google Location History (GLH), which is accessible on the Google Maps application through the “Your Timeline” option to get GPS tracking data. GLH is available on all mobile devices around the world with the Google Maps application installed. 

## Stages to process your data:

### - Data Source

Request your GLH JSON file from Google via [Google Takeout](https://takeout.google.com/)

### - JSON Transformation

Run the script to transform Google Location History (GLH) JSON files into CSV files

Pre-requisites to run the script:
   1. Check or create folders in your python directory: `code`, `dataJSON`
   2. Copy scripts [01JSON-Transformation.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/01JSON-Transformation.py) and [02APL-Processing.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/02APL-Processing.py) in the code directory
   3. Copy GLH JSON file in the `dataJSON` directory 
   4. Set `code` as your working directory
   5. Run script

### - APL Processing

Run the script to compute Activity Point Locations (APL). This script is automatically executed from script [01JSON-Transformation.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/01JSON-Transformation.py)

Pre-requisites in case you want to run the script separately: 
   1. Check or create folders in your python directory: `code`, `dataTransform`, `dataFinal`, `log` 
   2. Copy script [02APL-Processing.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/02APL-Processing.py) in the code directory
   3. Copy CSV file in the `dataTransform` directory
   4. Set `code` as your working directory
   5. Run script

## How to cite this project

Moncayo-Unda, Milton Giovanny (2021): Activity Point Location Data. figshare. Dataset. (https://doi.org/10.6084/m9.figshare.16727014.v1) 

## Having trouble?

Check the [paper documentation](https://docs.github.com/categories/github-pages-basics/) or [contact](mailto:mmoncayo@uce.edu.ec). I’ll help you sort it out.
