# Data Quality Evaluation
This project evaluates the quality of the Top 200 Datasets (by number of downloads) listed on the Government of Canada's OpenData Portal, but can also be used to validate any single dataset or CSV list of datasets against the TBS Data Quality Metrics.

## Installation
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

## Command Line
Once installed inside of your virtual environment, you can execute the code from the command line.  Depending on your desired mode, you can use the command line flags below to pass in the required parameters.

    Usage
        python main.py
            --mode {topN | csv | single}

                topN
                    no additional parameters

                csv
                    --inputfile [path]

                single
                    --de "description_en"
                    --df "description_fr"
                    --o  "owner_org"
                    --e  "maintainer_email"
                    --u  "url"
                    --f  "source_format"

            --cleanup
                remove all files in the temp_data folder when finished

Here are some examples for the CLI:

    Examples
        # SINGLE
        python main.py --mode single --de "Test English Description" --df "Test French Description" --o "Treasury Board" --e "your.email@canada.ca" --u "http://www.cic.gc.ca/opendata-donneesouvertes/data/IRCC_M_PRadmiss_0003_CSV.csv" --f csv
        
        python main.py --mode single --de "Test English Description" --df "Test French Description" --o "Treasury Board" --e "your.email@canada.ca" --u "http://www.cbsa-asfc.gc.ca/data/bwt-taf-2010-2014-eng.csv" --f csv

        # CSV
        python main.py --mode csv --inputfile "./temp_data/test-data.csv"

        # TopN
        python main.py --mode topN

### Top 200 Non-Spatial Datasets
This project's initial purpose was to evaluate data quality metrics on the Top 200 non-spatial datasets by total downloads on the open data portal.  It has been expanded to include additional functionality, however the Top 200 component still plays a major role.  Using the `--mode topN` flags will generate the Top 200 csv and will validate each dataset contained within the top 200 packages and produce a CSV output.

## API & Web Form
The `api-demo` folder contains a simple web form and python API to deliver data quality results in the browser.  It has its own list of requirements, so you will need to create a separate virtual environment under the api-demo directory and install the requirements from the /api-demo/requirements.txt file.  You'll find additional documentation in that folder.


