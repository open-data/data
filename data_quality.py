import shutil, sys, json
import pandas as pd
from textstat.textstat import textstat
from validate_email import validate_email
from datetime import datetime
from goodtables import validate
import data_quality_config as dqconfig
import data_quality_utils as dqutils

""" 
    Evaluating the datasets published on the open data portal using the open data 
    catalogue json lines file 
"""

output_file = 'dq_ratings_top_200.csv'

# Inspect the provided maintainer email and don't count the default @tbs email 
# addresses unless the owning organization is actually TBS
def validate_maintainer_email(org, email):
    if org == "Treasury Board of Canada Secretariat":
        is_email_valid = validate_email(email)
    else:
        if email.split('@')[-1].lower() == "tbs-sct.gc.ca":
            is_email_valid = False
        else:
            is_email_valid = validate_email(email)
    return 1 if is_email_valid else 0

# Compare the number of days since the last update against the expected update frequency
def frequency_date_check(d, m):
    if d == None:
        return 0
    else:
        updated_date = datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
        time_since_update = dqconfig.snapshot_end_date - updated_date
        if time_since_update.days <= m:
            return 1
        else:
            return 0

# Examine the specified update frequency and compare it against the last updated date
def validate_update_frequency(frequency, modified, published):
    if frequency in dqconfig.frequency_automatic_point:
        return 1
    else:
        try:
            max_days_since_update = dqconfig.frequency_lookup[frequency]
        except:
            print('Unknown frequency specified: {0}'.format(frequency))
            return 0

        try:
            return frequency_date_check(modified, max_days_since_update)
        except:
            print('Unable to parse last modified date which was specified as: {0}'.format(modified))
            try:
                return frequency_date_check(published, max_days_since_update)
            except:
                print('Unable to parse published date which was specified as: {0}'.format(published))
                return 0    

# Run the supplied string through the Flesch-Kincaid readability grade test
def validate_readability_english(d):
    score = textstat.flesch_kincaid_grade(d)
    if score <= 8:
        return 1
    else:
        return 0

# Load the Top 200 Non Spatial file.  Exit with an error if we can't find it. 
def get_top_200_non_spatial():
    try:
        df = pd.read_csv(dqconfig.top200_file, encoding=dqconfig.encoding_type)
        return df['id']
    except:
        sys.exit('Unable to find the Top 200 Non Spatial Datasets file.  Please run topN_nonspatial.py before running this script.')

# Attempt to download the gzipped data catalogue, decompress, and parse out the required information.  
# If we fail to download and extract the gzip and a local copy exists, the script will still run
def fetch_and_parse_catalogue(zip_url, expected_file):
    df = pd.DataFrame()
    datasets = []
    resources = []
    errors = []

    dqutils.get_and_extract_gzip(zip_url, expected_file)

    with open(expected_file, encoding=dqconfig.encoding_type) as f:
        print('Parsing the Catalogue')
        for line in f:
            data = json.loads(line)
            current_record = data.get('id')
            try:
                dataset_record = {
                    "record_id": data.get('id'),
                    "date_published": data.get('date_published'),
                    "date_modified": data.get('date_modified'),
                    "frequency": data.get('frequency'),
                    "owner_org": data['org_title_at_publication'].get('en'),
                    "maintainer_email": data.get('maintainer_email'),
                    "metadata_created": data.get('metadata_created'),
                    "metadata_modified": data.get('metadata_modified'),
                    "description_en": data['notes_translated'].get('en'),
                    "description_fr": data['notes_translated'].get('fr')
                }
                
                for r in data['resources']:
                    resource_record = {
                        "dataset_id": data.get('id'),
                        "resource_id": r.get('id'),
                        "package_id": r.get('package_id'),
                        "source_format": r.get('format'),
                        "resource_type": r.get('resource_type'),
                        "created": r.get('created'),
                        "state": r.get('state'),
                        "url": r.get('url'),
                        "url_type": r.get('url_type')
                    }
                    resources.append(resource_record)
                
                datasets.append(dataset_record)

            except:
                errors.append(current_record)
                pass
    
    print('>> Catalogue parsing complete')
    
    if len(datasets) > 0:
        df_datasets = pd.DataFrame(datasets)

        if len(resources) > 0:
            df_resources = pd.DataFrame(resources)
            df = pd.merge(left=df_datasets, right=df_resources, left_on='record_id', right_on='dataset_id')

    if len(errors) > 0:
        print('ERRORS: There were {0} JSON objects in the catalogue which were unable to be parsed'.format(len(errors)))
        print(errors)

    return df

# The goodtables report produces a 404 error if the URL for the resource can't 
# be loaded.  Use that to establish the valid_url metric
def gt_validate_url(gt_report):
    try:
        if report['tables'][0]['errors'][0]['message'][:3] == '404':
            return 0
        else:
            return 1
    except:
        return 1

# The goodtables report includes the detected encoding.  Validate that it is utf-8
def gt_validate_encoding(gt_report):
    try:
        if gt_report['tables'][0]['encoding'] == 'utf-8':
            return 1
        else:
            return 0
    except:
        return 0

# The goodtables report will evaluate CSV/XLS/JSON files to ensure they're valid
def gt_validate_format(gt_report):
    try:
        if gt_report['tables'][0]['valid'] == True:
            return 1
        else:
            return 0
    except:
        return 0

# Load the JSONL Catalogue and parse out the information we need
print('Loading the JSONL Catalogue')
df_catalogue = fetch_and_parse_catalogue(dqconfig.catalogue_zip_file, dqconfig.catalogue_file)

# Filter the catalogue down to our top 200
print('Loading the Top N Non-Spatial Datasets')
df_top200 = get_top_200_non_spatial()
df_quality = pd.merge(left=df_top200, right=df_catalogue, left_on='id', right_on='package_id')

# Calculate the Data Quality Metrics for our Top 200 datasets
print('Calculating Data Quality Metrics')

# Readability
print('>> Starting Readability Tests')
df_quality['readability_grade_en'] = df_quality['description_en'].apply(lambda x: textstat.flesch_kincaid_grade(x))
df_quality['valid_readability_en'] = df_quality['readability_grade_en'].apply(lambda x: 1 if x<=8 else 0)

# Maintainer Email
print('>> Starting Maintainer Email Tests')
df_quality['valid_maintainer_email'] = df_quality.apply(lambda x: validate_maintainer_email(x['owner_org'], x['maintainer_email']), axis=1)

# Update Frequency
print('>> Starting Readability Tests')
df_quality['valid_update_frequency'] = df_quality.apply(lambda x: validate_update_frequency(x['frequency'], x['date_modified'], x['date_published']), axis=1)

# Supporting Documentation
print('>> Starting Supporting Documentation Tests')
df_supporting_docs = df_quality.loc[df_quality['resource_type'].isin(dqconfig.supporting_documentation_resource_types)]
ids_with_supporting_docs = df_supporting_docs['id'].unique().tolist()
df_quality['valid_supporting_docs'] = df_quality['id'].apply(lambda x: 1 if x in ids_with_supporting_docs else 0)

# Goodtables evaluation for url, encoding, format, filetype, and schema
#TODO: Can I do this with lambdas or do I have to iterate the dataframe?
print('>> Starting Goodtables Evaluation')
goodtables_evaluation = []
for index, row in df_quality.iterrows():
    file_name = dqutils.get_filename_from_url(row['url'])
    file_extension = file_name.split('.')[-1].lower()
    if file_extension in dqconfig.goodtables_supported_file_types:
        gt_report = validate(row['url'])
        #TODO: look for a schema and validate
        dict_entry = {
            "gt_id": row['id'],
            "gt_r_id": row['resource_id'],
            "valid_url": gt_validate_url(gt_report),
            "valid_encoding": gt_validate_encoding(gt_report),
            "valid_format": gt_validate_format(gt_report),
            "valid_file_type": 1 if file_extension == row['source_format'].lower() else 0,
            "valid_schema": 0
        }
    else:
        dict_entry = {
            "gt_id": row['id'],
            "gt_r_id": row['resource_id'],
            "valid_encoding": 0,
            "valid_format": 0,
            "valid_file_type": 0,
            "valid_schema": 0
        }

    goodtables_evaluation.append(dict_entry)

# Merge the goodtables results back into the main dataframe
df_goodtables = pd.DataFrame(goodtables_evaluation)
df_quality = pd.merge(left=df_quality, right=df_goodtables, left_on='resource_id', right_on='gt_r_id')

# Write the final dataframe to CSV
print('Finalizing Output File')
df_quality.to_csv(output_file, index=None, header=True, encoding=dqconfig.encoding_type)

# Delete the temp_data_folder
if dqconfig.remove_temp_data:
    print('Removing Temporary Data')
    shutil.rmtree(dqconfig.temp_data_folder)