import shutil
import requests, zipfile, gzip, io
import json
import pandas as pd

""" Non-Spatial dataset analysis on the open data registry """

temp_data_folder = './temp_data/'
remove_temp_data = True
#NOTE: These links (downloads and visits) likely change each time the dataset is generated.  It'll need to be updated after each refresh.
#TODO: Do this properly by leveraging the CKAN API and the GA
downloads_file = 'https://open.canada.ca/data/dataset/2916fad5-ebcc-4c86-b0f3-4f619b29f412/resource/4ebc050f-6c3c-4dfd-817e-875b2caf3ec6/download/downloads-122019-122019.xls'
visits_file = 'https://open.canada.ca/data/dataset/2916fad5-ebcc-4c86-b0f3-4f619b29f412/resource/c14ba36b-0af5-4c59-a5fd-26ca6a1ef6db/download/visits-122019-122019.xls'
nonspatial_file = 'https://search.open.canada.ca/en/od/export/?sort=last_modified_tdt+desc&page=1&search_text=&od-search-portal=Open+Data&od-search-col=Non-Spatial&od-search-jur=Federal'
openness_zip_file = 'https://open.canada.ca/static/openness-details.csv.zip'
openness_file = temp_data_folder + 'openness-details.csv'
catalogue_zip_file = 'http://open.canada.ca/static/od-do-canada.jl.gz'
catalogue_file = temp_data_folder + 'od-do-canada.jl'
output_file = 'TopNonSpatialDatasets.csv'
output_size = 500
encoding_type = 'utf-8'


def excel_delete_and_merge_tabs(excel_file, tab_names):
    """ 
    Reads an excel file with multiple tabs, deletes specified named tabs, 
    and merges all tabs into a single pandas dataframe. 
    """
    
    data_wb = pd.read_excel(excel_file, sheet_name=None, skipfooter=1, encoding=encoding_type)
    
    for t in tab_names:
        del data_wb[t]

    df_list = [v for k,v in data_wb.items()] 
    return pd.concat(df_list, axis=0)

def get_and_extract_zip(zip_url):
    try:
        r = requests.get(zip_url)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(temp_data_folder)
    except:
        print('Error processing ZIP archive')
        pass

def get_and_extract_gzip(zip_url, output_file):
    gzip_name = zip_url.split('/')[-1]
    try:
        with open(temp_data_folder + gzip_name, 'wb') as f:
            r = requests.get(zip_url)
            f.write(r.content)
    except:
        print('Error downloading GZIP archive')
        pass
    
    try:
        with gzip.open(temp_data_folder + gzip_name, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    except:
        print('Error decoding GZIP archive')
        pass
            
def fetch_zipped_csv(zip_url, expected_file):
    """ 
    Fetches a zip file from a url, extracts zip contents to the temp_data_folder, 
    looks for the specified CSV file in the output and returns it as a pandas dataframe.  
    If the file isn't found, returns an empty dataframe.
    """

    get_and_extract_zip(zip_url)
    df = pd.DataFrame()

    try:
        df = pd.read_csv(expected_file, encoding=encoding_type)
    except:
        print('Error reading expected file')
        pass

    return df

def fetch_and_parse_catalogue(zip_url, expected_file):
    format_list = ['CSV', 'JSON', 'JSONL', 'XML', 'XLS', 'XLSX', 'XLSM', 'TXT', 'TAB', 'ZIP']
    df = pd.DataFrame()
    catalogue_data = []

    get_and_extract_gzip(zip_url, expected_file)

    with open(expected_file, encoding=encoding_type) as f:
        for line in f:
            data = json.loads(line)
            for r in data['resources']:
                dict_entry = {
                    "c_id": r['package_id'],
                    "source_format": r['format'],
                    "resource_type": r['resource_type']
                }
                catalogue_data.append(dict_entry)

    if len(catalogue_data) > 0:
        df = pd.DataFrame(catalogue_data)

        df['dataset_format'] = df.source_format.apply(lambda x: x.upper() if x.upper() in format_list else 'OTHER')
        df = df[df['resource_type'].isin(['dataset','api'])]
        df['dataset_format'] = pd.Categorical(df['dataset_format'], format_list.append('OTHER'))
        df = df[['c_id', 'dataset_format']]
        df = df.sort_values(['c_id','dataset_format'])
        df = df.groupby('c_id', as_index=False).first()

    return df


df_downloads = excel_delete_and_merge_tabs(downloads_file, ['Summary by departments', 'Top 100 Datasets'])
df_downloads.columns = ['d_id', 'd_title_en', 'd_title_fr', 'd_downloads']

df_visits = excel_delete_and_merge_tabs(visits_file, ['Summary by departments', 'Top 100 Datasets'])
df_visits.columns = ['v_id', 'v_title_en', 'v_title_fr', 'v_visits']

df_analysis = pd.merge(left=df_downloads, right=df_visits, left_on='d_id', right_on='v_id')
df_analysis = df_analysis[['d_id', 'd_title_en', 'd_downloads', 'v_visits']]

df_nonspatial = pd.read_csv(nonspatial_file, encoding=encoding_type)

df_merged = pd.merge(left=df_nonspatial, right=df_analysis, left_on='id_s', right_on='d_id')
df_merged.columns = ['id', 'owner_org_en', 'owner_org_fr', 'title_en', 'title_fr', 'desc_en', 'desc_fr', 'link_en', 'link_fr', 'id2', 'title_en_2', 'downloads', 'visits']

col_list = ['id', 'owner_org_en', 'title_en', 'desc_en', 'link_en', 'downloads', 'visits']

df = df_merged[col_list]

df_openness = fetch_zipped_csv(openness_zip_file, openness_file)
if not df_openness.empty:
    df_openness.columns = ['department', 'title', 'URL', 'openness_rating']
    df_openness[['e_url', 'f_url']] = df_openness['URL'].str.split('|', expand=True)
    df_openness['o_id'] = df_openness['e_url'].str.split('/').str[-1].str.strip()
    df_openness = df_openness[['o_id', 'openness_rating']]
    df = pd.merge(left=df, right=df_openness, left_on='id', right_on='o_id')
    col_list.append('openness_rating')
    df = df[col_list]

df_catalogue = fetch_and_parse_catalogue(catalogue_zip_file, catalogue_file)
if not df_catalogue.empty:
    df = pd.merge(left=df, right=df_catalogue, left_on='id', right_on='c_id')
    col_list.append('dataset_format')
    df = df[col_list]

df.sort_values(by='downloads', ascending=False).head(output_size).to_csv(output_file, index=None, header=True, encoding=encoding_type)

if remove_temp_data:
    shutil.rmtree(temp_data_folder)