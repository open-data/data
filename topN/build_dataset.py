import shutil, ssl, json
import requests, zipfile, gzip, io
import pandas as pd
from tbsdq import utilities as dqutils
from tbsdq import configuration as dqconfig
from topN import configuration as topnconfig


""" Non-Spatial dataset analysis on the open data registry """

def fetch_and_parse_catalogue(zip_url, expected_file):
    format_list = ['CSV', 'JSON', 'JSONL', 'XML', 'XLS', 'XLSX', 'XLSM', 'TXT', 'TAB', 'ZIP']
    df = pd.DataFrame()
    catalogue_data = []

    dqutils.get_and_extract_gzip(zip_url, expected_file)

    try:
        with open(expected_file, encoding=dqconfig.encoding_type) as f:
            for line in f:
                data = json.loads(line)
                for r in data['resources']:
                    dict_entry = {
                        "c_id": r['package_id'],
                        "source_format": r['format'],
                        "resource_type": r['resource_type']
                    }
                    catalogue_data.append(dict_entry)

    except:
        print('Error reading expected file: {0}'.format(expected_file))
        pass

    if len(catalogue_data) > 0:
        df = pd.DataFrame(catalogue_data)

        df['dataset_format'] = df.source_format.apply(lambda x: x.upper() if x.upper() in format_list else 'OTHER')
        df = df[df['resource_type'].isin(['dataset','api'])]
        df['dataset_format'] = pd.Categorical(df['dataset_format'], format_list.append('OTHER'))
        df = df[['c_id', 'dataset_format']]
        df = df.sort_values(['c_id','dataset_format'])
        df = df.groupby('c_id', as_index=False).first()

    return df

def build_top_N_dataset():
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        output_file = topnconfig.topN_file
        output_size = topnconfig.topN_size

        df_downloads = dqutils.excel_delete_and_merge_tabs(topnconfig.downloads_file, ['Summary by departments', 'Top 100 Datasets'])
        df_downloads.columns = ['d_id', 'd_title_en', 'd_title_fr', 'd_downloads']

        df_visits = dqutils.excel_delete_and_merge_tabs(topnconfig.visits_file, ['Summary by departments', 'Top 100 Datasets'])
        df_visits.columns = ['v_id', 'v_title_en', 'v_title_fr', 'v_visits']

        df_analysis = pd.merge(left=df_downloads, right=df_visits, left_on='d_id', right_on='v_id')
        df_analysis = df_analysis[['d_id', 'd_title_en', 'd_downloads', 'v_visits']]

        df_nonspatial = pd.read_csv(topnconfig.nonspatial_file, encoding=dqconfig.encoding_type)

        df_merged = pd.merge(left=df_nonspatial, right=df_analysis, left_on='id_s', right_on='d_id')
        df_merged.columns = ['id', 'owner_org_en', 'owner_org_fr', 'title_en', 'title_fr', 'desc_en', 'desc_fr', 'link_en', 'link_fr', 'id2', 'title_en_2', 'downloads', 'visits']

        col_list = ['id', 'owner_org_en', 'title_en', 'desc_en', 'link_en', 'downloads', 'visits']

        df = df_merged[col_list]

        df_openness = dqutils.fetch_zipped_csv(topnconfig.openness_zip_file, topnconfig.openness_file)
        if not df_openness.empty:
            df_openness.columns = ['department', 'title', 'URL', 'openness_rating']
            df_openness[['e_url', 'f_url']] = df_openness['URL'].str.split('|', expand=True)
            df_openness['o_id'] = df_openness['e_url'].str.split('/').str[-1].str.strip()
            df_openness = df_openness[['o_id', 'openness_rating']]
            df = pd.merge(left=df, right=df_openness, left_on='id', right_on='o_id')
            col_list.append('openness_rating')
            df = df[col_list]

        df_catalogue = fetch_and_parse_catalogue(topnconfig.catalogue_zip_file, topnconfig.catalogue_file)
        if not df_catalogue.empty:
            df = pd.merge(left=df, right=df_catalogue, left_on='id', right_on='c_id')
            col_list.append('dataset_format')
            df = df[col_list]

        df_user_ratings = pd.read_csv(topnconfig.user_ratings_file, encoding=dqconfig.encoding_type)
        df_user_ratings.columns = ['j1', 'j2', 'ur_id', 'user_rating_score', 'user_rating_count', 'l1', 'l2']
        df_user_ratings = df_user_ratings[['ur_id', 'user_rating_score', 'user_rating_count']]
        df = pd.merge(left=df, right=df_user_ratings, left_on='id', right_on='ur_id')
        col_list.append('user_rating_score')
        col_list.append('user_rating_count')
        df = df[col_list]

        df.sort_values(by='downloads', ascending=False).head(output_size).to_csv(output_file, index=None, header=True, encoding=dqconfig.encoding_type)

        if dqconfig.remove_temp_data:
            shutil.rmtree(dqconfig.temp_data_folder)
    except:
        raise
