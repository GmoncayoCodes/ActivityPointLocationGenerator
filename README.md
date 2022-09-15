# Welcome to AnLoCOV Project

Anonymised Longitudinal COVID dataset

GPS data collection using mobile devices is of particular interest. This data provides detailed information on people's daily movements due to devices' ubiquity and daily use. 

This project contain scripts to compute Activity Point Location (APL) from mobile devices' GPS tracking. We use Google Location History (GLH), which is accessible on the Google Maps application through the “Your Timeline” option to get GPS tracking data. GLH is available on all mobile devices around the world with the Google Maps application installed. 

## Stages to process the data:

### - Data Collection

Request your GLH JSON file from Google via [Google Takeout](https://takeout.google.com/)

### - Data Transformation

Run the script to transform Google Location History (GLH) JSON files into CSV files

Pre-requisites to run the script:
   1. Check or create folders in your python directory: `code`, `dataJSON`
   2. Copy scripts [01JSON-Transformation.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/01JSON-Transformation.py) and [02AnLoCOV-Processing.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/02AnLoCOV-Processing.py) in the code directory
   3. Copy GLH JSON file in the `dataJSON` directory (Replace test.json) 
   4. Set `code` as your working directory
   5. Run script

### - AnLoCOV Processing

Run the script to compute AnLoCOV dataset. This script is automatically executed from script [01JSON-Transformation.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/01JSON-Transformation.py)

Pre-requisites in case you want to run the script separately: 
   1. Check or create folders in your python directory: `code`, `dataTransform`, `dataFinal`, `log` 
   2. Copy script [02AnLoCOV-Processing.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/02AnLoCOV-Processing.py) in the code directory
   3. Copy CSV file in the `dataTransform` directory
   4. Set `code` as your working directory
   5. Run script

## How to cite this project

Moncayo Unda, Milton Giovanny; Van Droogenbroeck, Marc; Saadi, Ismaïl; Cools, Mario (2022), “AnLoCOV”, Mendeley Data, V2, [doi: 10.17632/vk77k9gvg3.2](https://doi.org/10.17632/vk77k9gvg3.2)

## Having trouble?

Check the [paper documentation](https://docs.github.com/categories/github-pages-basics/) or [contact](mailto:mmoncayo@uce.edu.ec). I’ll help you sort it out.
