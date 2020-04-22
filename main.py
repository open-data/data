import sys, shutil, argparse, csv
import pandas as pd
from tbsdq import data_quality as dq
from topN import build_dataset as topnbuild
from topN import utilities as topnutils
from topN import configuration as topnconfig

"""
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

Examples
    # SINGLE
    python main.py --mode single --de "Test English Description" --df "Test French Description" --o "Treasury Board" --e "your.email@canada.ca" --u "http://www.cic.gc.ca/opendata-donneesouvertes/data/IRCC_M_PRadmiss_0003_CSV.csv" --f csv
    python main.py --mode single --de "Test English Description" --df "Test French Description" --o "Treasury Board" --e "your.email@canada.ca" --u "http://www.cbsa-asfc.gc.ca/data/bwt-taf-2010-2014-eng.csv" --f csv

    # CSV
    python main.py --mode csv --inputfile "./temp_data/test-data.csv"

    # TopN
    python main.py --mode topN

"""

parser = argparse.ArgumentParser(description='TBS Data Quality Evaluation Tool')
parser.add_argument("--mode", "--m", choices=["topN", "csv", "single"], default="topN", type=str, help="specify the mode of execution")
parser.add_argument("--inputfile", "--i", type=str, help="path to the input file (csv mode only)")
parser.add_argument("--de", type=str, help="description in English (single mode only)")
parser.add_argument("--df", type=str, help="description in French (single mode only)")
parser.add_argument("--o", type=str, help="the owning organization for the dataset (single mode only)")
parser.add_argument("--e", type=str, help="the maintainer email address for the dataset (single mode only)")
parser.add_argument("--u", type=str, help="the full URL to the dataset (single mode only)")
parser.add_argument("--f", type=str, help="the expected file format (e.g. csv, xls, xml) (single mode only)")
parser.add_argument("--cleanup", action="store_true", default=False, help="remove all files in the temp_data directory when finished")
args = parser.parse_args()

encoding_type = 'utf-8'
temp_data_folder = './temp_data'
remove_temp_data = args.cleanup
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
    df_quality.to_csv(dq_ratings_output_file, index=None, header=True, encoding=encoding_type)
    print('Results written to {0:s}.  Exiting'.format(dq_ratings_output_file))

elif validation_mode == 'csv':
    dq_ratings_output_file = 'dq_ratings_custom_list.csv'

    try:
        # Send it to core validation
        df_quality = dq.dq_validate(args.inputfile, 'csv') 
    except:
        sys.exit('>> Unable to read the specified csv file.  Exiting')

    try:
        # Write the output file
        print('Finalizing Output File')
        df_quality.to_csv(dq_ratings_output_file, index=None, header=True, encoding=encoding_type)
        print('Results written to {0:s}.  Exiting'.format(dq_ratings_output_file))
    except:
        sys.exit('>> Unable to write the specified csv file.  Exiting')

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

    df_quality = dq.dq_validate(single_record, 'single')
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

    print('>> TBS Data Quality Score:\n\tReadability (EN):\t{0}\n\tReadability (FR):\t{1}\n\tValid URL:\t\t{2}\n\tValid File Type:\t{3}\n\tValid Encoding:\t\t{4}\n\tValid Format:\t\t{5}'.format(
        df_quality['valid_readability_en'][0],
        df_quality['valid_readability_fr'][0],
        df_quality['valid_url'][0],
        df_quality['valid_file_type'][0],
        df_quality['valid_encoding'][0],
        df_quality['valid_format'][0]
    ))

else:
    sys.exit('Invalid mode specified.  Run the command again with --help for more information.')

# Delete the temp_data_folder
if remove_temp_data:
    print('Removing Temporary Data')
    shutil.rmtree(temp_data_folder)
