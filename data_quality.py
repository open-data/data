import shutil, sys, json
import pandas as pd
from pandas import Panel
from textstat.textstat import textstat
from validate_email import validate_email
from datetime import datetime
from goodtables import validate
from tqdm.auto import tqdm
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
    if org.startswith("Treasury Board"):
        is_email_valid = validate_email(email)
    else:
        if email.split('@')[-1].lower() == "tbs-sct.gc.ca":
            is_email_valid = False
        else:
            is_email_valid = validate_email(email)
    return 1 if is_email_valid else 0

# Compare the number of days since the last update against the expected update frequency
def frequency_date_check(resource_modified, metadata_modified, max_days_since_update):
    try:
        resource_updated_date = datetime.strptime(resource_modified, '%Y-%m-%dT%H:%M:%S.%f')
        time_since_resource_update = dqconfig.snapshot_end_date - resource_updated_date
        if time_since_resource_update.days <= max_days_since_update:
            return 1
    except:
        return 0
    try:
        metadata_updated_date = datetime.strptime(metadata_modified, '%Y-%m-%dT%H:%M:%S.%f')
        time_since_metadata_update = dqconfig.snapshot_end_date - metadata_updated_date
        if time_since_metadata_update.days <= max_days_since_update:
            return 1 
    except:
        return 0
    return 0

# Examine the specified update frequency and compare it against the last updated date
def validate_update_frequency(frequency, resource_modified, metadata_modified):
    if frequency in dqconfig.frequency_automatic_point:
        return 1
    else:
        try:
            max_days_since_update = dqconfig.frequency_lookup[frequency]
        except:
            print('Unknown frequency specified: {0}'.format(frequency))
            return 0
        try:
            return frequency_date_check(resource_modified, metadata_modified, max_days_since_update)
        except:
            print('Unable to parse last modified date which was specified as: {0} AND '.format(resource_modified, metadata_modified))
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
        sys.exit('>> Unable to find the Top 200 Non Spatial Datasets file.  Please run topN_nonspatial.py before running this script.')

# Attempt to download the gzipped data catalogue, decompress, and parse out the required information.  
# If we fail to download and extract the gzip and a local copy exists, the script will still run
def fetch_and_parse_catalogue(zip_url, expected_file):
    df = pd.DataFrame()
    datasets = []
    resources = []
    errors = []

    dqutils.get_and_extract_gzip(zip_url, expected_file)

    with open(expected_file, encoding=dqconfig.encoding_type) as f:
        print('>> Expected file found.  Parsing the Catalogue')
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
                        "last_modified": r.get('last_modified'),
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
        print('>> ERRORS: There were {0} JSON objects in the catalogue which were unable to be parsed'.format(len(errors)))
        print(errors)

    return df

# The goodtables report produces a 404 error if the URL for the resource can't 
# be loaded.  Use that to establish the valid_url metric
def gt_validate_url(gt_report):
    try:
        return 0 if gt_report['tables'][0]['errors'][0]['message'][:3] in dqconfig.bad_http_status else 1
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

def validate_file_type(url_type, source_type, url_valid):
    if url_type == source_type:
        return 1
    elif url_type == 'xlsx':
        return 1 if source_type == 'xls' else 0
    elif source_type == 'other':
        return 0 if url_type in dqconfig.registry_formats else 1
    elif url_type in ['api', 'html']:
        return url_valid
    elif "=" in url_type:
        for y in dqconfig.registry_formats:
            if y in url_type and y == source_type:
                return 1
        return 0
    else:
        return 0

# Load the JSONL Catalogue and parse out the information we need
print('Loading the JSONL Catalogue')
df_catalogue = fetch_and_parse_catalogue(dqconfig.catalogue_zip_file, dqconfig.catalogue_file)
#DEBUG
#df_catalogue.to_csv('debug_parsed_catalogue.csv', index=None, header=True, encoding=dqconfig.encoding_type)


# Filter the catalogue down to our top 200
print('Loading the Top N Non-Spatial Datasets')
df_top200 = get_top_200_non_spatial()
df_quality = pd.merge(left=df_top200, right=df_catalogue, left_on='id', right_on='package_id')

# Calculate the Data Quality Metrics for our Top 200 datasets
print('Calculating Data Quality Metrics')

# Supporting Documentation
print('>> Starting Supporting Documentation Tests')
df_supporting_docs = df_quality.loc[df_quality['resource_type'].isin(dqconfig.supporting_documentation_resource_types)]
ids_with_supporting_docs = df_supporting_docs['id'].unique().tolist()
df_quality['valid_supporting_docs'] = df_quality['id'].apply(lambda x: 1 if x in ids_with_supporting_docs else 0)

# Filter down to just datasets.  We only need the other entries for supporting documentation checks.
df_quality = df_quality[df_quality['resource_type'] == 'dataset']

# Readability
print('>> Starting Readability Tests')
df_quality['readability_grade_en'] = df_quality['description_en'].apply(lambda x: textstat.flesch_kincaid_grade(x))
df_quality['valid_readability_en'] = df_quality['readability_grade_en'].apply(lambda x: 1 if x<=8 else 0)
df_quality['readability_grade_fr'] = df_quality['description_fr'].apply(lambda x: textstat.flesch_kincaid_grade(x))
df_quality['valid_readability_fr'] = df_quality['readability_grade_fr'].apply(lambda x: 1 if x<=8 else 0)

# Maintainer Email
print('>> Starting Maintainer Email Tests')
df_quality['valid_maintainer_email'] = df_quality.apply(lambda x: validate_maintainer_email(x['owner_org'], x['maintainer_email']), axis=1)

# Update Frequency
# 
# We're only looking to see if the latest file meets the specified update frequency so we group by ID 
# and take the MAX and overwrite the other resources. We may want to extend this in the future to 
# check frequency for each historic resource.
# 
# TODO: last_modified appears to always be null.  created always has a value so using that for now.
print('>> Starting Frequency Tests')
df_quality['valid_update_frequency'] = df_quality.apply(lambda x: validate_update_frequency(x['frequency'], x['created'], x['metadata_modified']), axis=1)
df_quality['valid_update_frequency_max'] = df_quality.groupby(['id'])['valid_update_frequency'].transform(max)
df_quality['valid_update_frequency'] = df_quality['valid_update_frequency_max']

# Goodtables evaluation for url, encoding, format, and filetype
print('>> Starting Goodtables Evaluation')
#TODO: Investigate goodtables batch processing
tqdm.pandas(desc="Goodtables Validation Progress")
df_quality['goodtables_report'] = df_quality['url'].progress_apply(lambda x: validate(x))
#df_quality['valid_file_type'] = df_quality.apply(lambda x: 1 if dqutils.get_filename_from_url(x['url']).split('.')[-1].lower() == x['source_format'].lower() else 0, axis=1)
df_quality['valid_url'] = df_quality['goodtables_report'].apply(lambda x: gt_validate_url(x))
df_quality['valid_file_type'] = df_quality.apply(lambda x: validate_file_type(dqutils.get_filename_from_url(x['url']).split('.')[-1].lower(), x['source_format'].lower(), x['valid_url']), axis=1)
df_quality['valid_encoding'] = df_quality['goodtables_report'].apply(lambda x: gt_validate_encoding(x))
df_quality['valid_format'] = df_quality['goodtables_report'].apply(lambda x: gt_validate_format(x))

df_quality.to_csv('debug_goodtables.csv', index=None, header=True, encoding=dqconfig.encoding_type)

# Add the metadata and resource quality scores as standalone fields
print('>> Getting averages and maximums')
df_quality['metadata_quality'] = df_quality.apply(lambda x: x['valid_update_frequency'] + x['valid_supporting_docs'] + x['valid_maintainer_email'] + x['valid_readability_en'], axis=1)
df_quality['resource_quality'] = df_quality.apply(lambda x: x['valid_url'] + x['valid_file_type'] + x['valid_format'] + x['valid_encoding'], axis=1)

# Get MAX Score for package
df_quality['metadata_quality_max'] = df_quality.groupby(['id'])['metadata_quality'].transform(max)
df_quality['resource_quality_max'] = df_quality.groupby(['id'])['resource_quality'].transform(max)

# Get MIN Score for package
df_quality['metadata_quality_min'] = df_quality.groupby(['id'])['metadata_quality'].transform(min)
df_quality['resource_quality_min'] = df_quality.groupby(['id'])['resource_quality'].transform(min)

# Get AVG Score for package
df_quality['metadata_quality_avg'] = df_quality.groupby('id')['metadata_quality'].transform('mean')
df_quality['resource_quality_avg'] = df_quality.groupby('id')['resource_quality'].transform('mean')

# Get latest file score
#TODO: Figure out why I get a key error for last_updated.  It's null for the entire top 200 so low priority.
df_quality['resource_last_modified'] = df_quality['created']
df_latest = df_quality.sort_values(['resource_last_modified', 'metadata_quality', 'resource_quality']).groupby('id').tail(1)
df_latest = df_latest[['id', 'metadata_quality', 'resource_quality']]
df_latest.columns = ['latest_id', 'metadata_quality_latest', 'resource_quality_latest']
df_quality = pd.merge(left=df_quality, right=df_latest, left_on='id', right_on='latest_id')

# Trim back the column list
df_quality = df_quality[['id', 'resource_id', 'date_published', 'date_modified', 'frequency', 'owner_org', 'maintainer_email', 'metadata_created', \
    'metadata_modified', 'description_en', 'description_fr', 'source_format', 'resource_type', 'created', 'last_modified', 'url', 'url_type', \
    'readability_grade_en', 'readability_grade_fr', 'valid_readability_en', 'valid_readability_fr', 'valid_maintainer_email', \
    'valid_update_frequency', 'valid_supporting_docs', 'valid_file_type', 'valid_url', 'valid_encoding', 'valid_format', \
    'metadata_quality', 'resource_quality', 'metadata_quality_min', 'resource_quality_min', 'metadata_quality_max', 'resource_quality_max', \
    'metadata_quality_avg', 'resource_quality_avg', 'metadata_quality_latest', 'resource_quality_latest']]

# Write the final dataframe to CSV
print('Finalizing Output File')
df_quality.to_csv(output_file, index=None, header=True, encoding=dqconfig.encoding_type)

# Delete the temp_data_folder
if dqconfig.remove_temp_data:
    print('Removing Temporary Data')
    shutil.rmtree(dqconfig.temp_data_folder)
