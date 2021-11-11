# Welcome to Activity Point Location (APL) Project

GPS data collection using mobile devices is of particular interest. This data provides detailed information on people's daily movements due to devices' ubiquity and daily use. This project contain scripts to compute Activity Point Location (APL) from mobile devices' GPS tracking. We use Google Location History (GLH), which is accessible on the Google Maps application through the “Your Timeline” option to get GPS tracking data. GLH is available on all mobile devices around the world with the Google Maps application installed. 

Stages to process your data:

## Data Source

Request your GLH JSON data from Google via [Google Takeout](https://takeout.google.com/)


## JSON Transformation

Script to transform Google Location History (GLH) JSON files into CSV files
Clone the code from Github [here](git@github.com:GmoncayoCodes/ActivityPointLocationGenerator.git)

Pre-requisites to run the script:
   1. Check or create folders in your python directory: code, dataJSON
   2. Copy scripts [01JSON-Transformation.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/01JSON-Transformation.py) and [02APL-Processing.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/02APL-Processing.py) in the code directory
   3. Copy GLH JSON file in the dataJSON directory 
   4. Set the folder code as your working directory
   5. Run script


## APL Processing

Script to compute Activity Point Locations (APL). This script is automatically executed from script [01JSON-Transformation.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/01JSON-Transformation.py)
Clone the code from Github [here](git@github.com:GmoncayoCodes/ActivityPointLocationGenerator.git)

Pre-requisites in case you want to run the script separately: 
   1. Check or create folders in your python directory: code, dataTransform, dataFinal, log 
   2. Copy script [02APL-Processing.py](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/blob/main/code/02APL-Processing.py) in the code directory
   3. Copy CSV file in the dataTransform directory
   4. Set the folder code as your working directory
   5. Run script






You can use the [editor on GitHub](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/edit/main/README.md) to maintain and preview the content for your website in Markdown files.

Whenever you commit to this repository, GitHub Pages will run [Jekyll](https://jekyllrb.com/) to rebuild the pages in your site, from the content in your Markdown files.

### Markdown

Markdown is a lightweight and easy-to-use syntax for styling your writing. It includes conventions for

```markdown
Syntax highlighted code block

# Header 1
## Header 2
### Header 3

- Bulleted
- List

1. Numbered
2. List

**Bold** and _Italic_ and `Code` text

[Link](url) and ![Image](src)
```

For more details see [GitHub Flavored Markdown](https://guides.github.com/features/mastering-markdown/).

### Jekyll Themes

Your Pages site will use the layout and styles from the Jekyll theme you have selected in your [repository settings](https://github.com/GmoncayoCodes/ActivityPointLocationGenerator/settings/pages). The name of this theme is saved in the Jekyll `_config.yml` configuration file.

### Support or Contact

Having trouble with Pages? Check out our [documentation](https://docs.github.com/categories/github-pages-basics/) or [contact support](https://support.github.com/contact) and we’ll help you sort it out.
