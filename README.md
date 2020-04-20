# Data Quality Evaluation
This project evaluates the quality of the Top 200 Datasets (by number of downloads) listed on the Government of Canada's OpenData Portal.

## Project Setup
1. This is a Python project.  For it to run, you must have [Python installed](https://www.python.org/downloads/) on your system.
1. Once Python is installed, open Powershell/Git Bash/Terminal and change to the directory where you'd like to keep this code base (e.g. `cd C:\Code`).
1. Install Python Virtual Environments
    * `pip install virtualenv`
1. Use git to clone this repository
    * `git clone <url_of_the_repository> <local_directory_name>`
1. Create and activate a virtual environment
    * `cd <local_directory_name>`
    * `virtualenv venv`
    * `venv/Scripts/activate`
        * On MacOS and Linux you'll need to run `source venv/Scripts/activate`
* Once you've activatated the virtual environment, Install the project requirements
    * `pip install -r requirements.txt`

## Top 200 Non-Spatial Datasets
This project is designed to evaluate data quality metrics on non-spatial datasets.  The `topN_nonspatial.py` script will generate the list of Top 200 non-spatial datasets for use throughout the rest of the processing.  
