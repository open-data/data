import shutil, sys, json
import pandas as pd
from pandas import Panel
from goodtables import validate
from tqdm.auto import tqdm
from tbsdq.tbsdq import configuration as dqconfig
from tbsdq.tbsdq import utilities as dqutils
from tbsdq.tbsdq import validation as dqvalidate


""" 
    Evaluating the datasets published on the open data portal using the open data 
    catalogue json lines file 
"""

def run_common_validation(df_quality):
    # Readability
    print('>> Starting Readability Tests')
    df_quality['readability_grade_en'] = df_quality['description_en'].apply(lambda x: dqvalidate.get_readability_grade(x))
    df_quality['valid_readability_en'] = df_quality['readability_grade_en'].apply(lambda x: 1 if x<=dqconfig.readability_pass_en else 0)
    df_quality['readability_grade_fr'] = df_quality['description_fr'].apply(lambda x: dqvalidate.get_readability_grade(x))
    df_quality['valid_readability_fr'] = df_quality['readability_grade_fr'].apply(lambda x: 1 if x<=dqconfig.readability_pass_fr else 0)

    # Maintainer Email
    print('>> Starting Maintainer Email Tests')
    df_quality['valid_maintainer_email'] = df_quality.apply(lambda x: dqvalidate.validate_maintainer_email(x['owner_org'], x['maintainer_email']), axis=1)

    # Goodtables evaluation for url, encoding, format, and filetype
    print('>> Starting Goodtables Evaluation')
    #TODO: Investigate goodtables batch processing
    tqdm.pandas(desc="Goodtables Validation Progress")
    df_quality['goodtables_report'] = df_quality['url'].progress_apply(lambda x: validate(x))
    df_quality['valid_url'] = df_quality['goodtables_report'].apply(lambda x: dqvalidate.gt_validate_url(x))
    df_quality['valid_file_type'] = df_quality.apply(lambda x: dqvalidate.validate_file_type(dqutils.get_filename_from_url(x['url']).split('.')[-1].lower(), x['source_format'].lower(), x['valid_url']), axis=1)
    df_quality['valid_encoding'] = df_quality['goodtables_report'].apply(lambda x: dqvalidate.gt_validate_encoding(x))
    df_quality['valid_format'] = df_quality['goodtables_report'].apply(lambda x: dqvalidate.gt_validate_format(x))

    return df_quality

def run_topN_validation(df_target, cat_zip, cat_file):
    # Load the JSONL Catalogue and parse out the information we need
    print('Loading the JSONL Catalogue')
    df_catalogue = dqutils.fetch_and_parse_catalogue(cat_zip, cat_file)

    # Filter the catalogue down to our top 200
    print('Processing the Top N Non-Spatial Datasets')
    df_top200 = df_target
    df_quality = pd.merge(left=df_top200, right=df_catalogue, left_on='id', right_on='package_id')

    # Supporting Documentation
    print('>> Starting Supporting Documentation Tests')
    df_supporting_docs = df_quality.loc[df_quality['resource_type'].isin(dqconfig.supporting_documentation_resource_types)]
    ids_with_supporting_docs = df_supporting_docs['id'].unique().tolist()
    df_quality['valid_supporting_docs'] = df_quality['id'].apply(lambda x: 1 if x in ids_with_supporting_docs else 0)

    # Filter down to just datasets.  We only need the other entries for supporting documentation checks.
    df_quality = df_quality[df_quality['resource_type'] == 'dataset']

    # Update Frequency
    # 
    # We're only looking to see if the latest file meets the specified update frequency so we group by ID 
    # and take the MAX and overwrite the other resources. We may want to extend this in the future to 
    # check frequency for each historic resource.
    # 
    # TODO: last_modified appears to always be null.  created always has a value so using that for now.
    print('>> Starting Frequency Tests')
    df_quality['valid_update_frequency'] = df_quality.apply(lambda x: dqvalidate.validate_update_frequency(x['frequency'], x['created'], x['metadata_modified']), axis=1)
    df_quality['valid_update_frequency_max'] = df_quality.groupby(['id'])['valid_update_frequency'].transform(max)
    df_quality['valid_update_frequency'] = df_quality['valid_update_frequency_max']

    df_quality = run_common_validation(df_quality)

    # Calculate the Data Quality Metrics for our Top 200 datasets
    print('Calculating Data Quality Metrics')

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

    return df_quality
