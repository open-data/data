import sys, shutil, argparse, json
import pandas as pd
from tbsdq.tbsdq import data_quality as dq
from tbsdq.tbsdq import configuration as dqconfig
from topN import build_dataset as topnbuild
from topN import utilities as topnutils
from topN import configuration as topnconfig

"""
description_en
description_fr
owner_org
maintainer_email
url
source_format

--mode {topN | csv | single | json}

csv
--inputfile [path]

json
--inputfile [path or json string]

single
--de "description_en"
--df "description_fr"
--o  "owner_org"
--e  "maintainer_email"
--u  "url"
--f  "format"

"""

parser = argparse.ArgumentParser(description='TBS Data Quality Evaluation Tool')
parser.add_argument("--mode", "--m", choices=["topN", "csv", "single", "json"], default="topN", type=str, help="specify the mode of execution")
parser.add_argument("--inputfile", "--i", type=str, help="path to the input file (csv or json mode only)")
parser.add_argument("--de", type=str, help="description in English (single mode only)")
parser.add_argument("--df", type=str, help="description in French (single mode only)")
parser.add_argument("--o", type=str, help="the owning organization for the dataset (single mode only)")
parser.add_argument("--e", type=str, help="the maintainer email address for the dataset (single mode only)")
parser.add_argument("--u", type=str, help="the full URL to the dataset (single mode only)")
parser.add_argument("--f", type=str, help="the expected file format (e.g. csv, xls, xml) (single mode only)")
args = parser.parse_args()

# DEBUG SINGLE
"""
args.mode = "single"
args.de = "Test English Description"
args.df = "Test French Description"
args.o = "Treasury Board"
args.e = "mdsisk@gmail.com"
#args.u = "http://www.cbsa-asfc.gc.ca/data/bwt-taf-2010-2014-eng.csv" #ERRORS
args.u = "http://www.cic.gc.ca/opendata-donneesouvertes/data/IRCC_M_PRadmiss_0003_CSV.csv" #CLEAN
args.f = "csv"
"""

validation_mode = args.mode

# Top 200
if validation_mode == 'topN':
    dq_ratings_output_file = 'dq_ratings_top_N.csv'

    # Load the Top 200 Non Spatial file.  Exit with an error if we can't find or build it. 
    try:
        df_topN = topnutils.get_top_N_non_spatial()
    except:
        sys.exit('>> An error occured trying to read or build the Top N dataset.  Exiting')

    df_quality = dq.run_topN_validation(df_topN, topnconfig.catalogue_zip_file, topnconfig.catalogue_file)

    # Write the final dataframe to CSV
    print('Finalizing Output File')
    df_quality.to_csv(dq_ratings_output_file, index=None, header=True, encoding=dqconfig.encoding_type)

elif validation_mode == 'csv':
    dq_ratings_output_file = 'dq_ratings_custom_list.csv'
    # Load the CSV
    try:
        df_csv = pd.read_csv(args.inputfile, encoding=dqconfig.encoding_type)
    except:
        sys.exit('>> Unable to read the specified csv file.  Exiting')

    #TODO: Make sure we have the required headers

    # Send it to core validation
    df_quality = dq.run_common_validation(df_csv)
   
    # Write the output file
    df_quality.to_csv(dq_ratings_output_file, index=None, header=True, encoding=dqconfig.encoding_type)

elif validation_mode == 'json':
    print('Not implemented')

elif validation_mode == 'single':
    try:
        single_record = {
            'description_en': args.de,
            'description_fr': args.df,
            'owner_org': args.o,
            'maintainer_email': args.e,
            'url': args.u,
            'source_format': args.f
        }
    except:
        sys.exit('When using the single mode, description_en (--de), description_fr (--df), owner_org (--o). maintainer_email (--e), url (--u), and format (--f) are all required.  Run the command again with --help for more information.')

    df_quality = dq.run_common_validation(pd.DataFrame([single_record]))
    gt_report = df_quality['goodtables_report'][0]
  
    print('>> Data Quality Report\n\tStructure:\t{0}\n\tEncoding:\t{1} ({2})\n\tRow Count:\t{3}\n\tError Count:\t{4}'.format(
        'Valid' if gt_report['tables'][0]['valid'] == True else 'INVALID',
        gt_report['tables'][0]['encoding'],
        'Valid' if gt_report['tables'][0]['encoding'].startswith('utf-8') else 'INVALID',
        gt_report['tables'][0]['row-count'],
        gt_report['tables'][0]['error-count']
    ))
    errors = gt_report['tables'][0]['errors']
    if len(errors) > 0:
        print('\tErrors:')
        for e in errors:
            print('\t\t{0}'.format(e['message']))

else:
    sys.exit('Invalid mode specified.  Run the command again with --help for more information.')

# Delete the temp_data_folder
if dqconfig.remove_temp_data:
    print('Removing Temporary Data')
    shutil.rmtree(dqconfig.temp_data_folder)
