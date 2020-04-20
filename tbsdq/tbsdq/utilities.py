import pandas as pd
import shutil
import requests, zipfile, gzip, io, json
from tbsdq.tbsdq import configuration as dqconfig

def get_and_extract_zip(zip_url):
    try:
        r = requests.get(zip_url)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(dqconfig.temp_data_folder)
    except:
        print('>> Error processing ZIP archive: {0}'.format(zip_url))
        pass

def get_and_extract_gzip(zip_url, output_file):
    gzip_name = zip_url.split('/')[-1]
    try:
        r = requests.get(zip_url)
        with open(dqconfig.temp_data_folder + gzip_name, 'wb') as f:
            f.write(r.content)
    except:
        print('>> Error downloading GZIP archive: {0}'.format(gzip_name))
        pass
    
    try:
        with gzip.open(dqconfig.temp_data_folder + gzip_name, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    except:
        print('>> Error decoding GZIP archive: {0}'.format(gzip_name))
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
        df = pd.read_csv(expected_file, encoding=dqconfig.encoding_type)
    except:
        print('>> Error reading expected file: {0}'.format(expected_file))
        pass

    return df

def get_filename_from_url(url):
    return url.split('/')[-1].lower()

def excel_delete_and_merge_tabs(excel_file, tab_names):
    """ 
    Reads an excel file with multiple tabs, deletes specified named tabs, 
    and merges all tabs into a single pandas dataframe. 
    """
    
    data_wb = pd.read_excel(excel_file, sheet_name=None, skipfooter=1, encoding=dqconfig.encoding_type)
    
    for t in tab_names:
        del data_wb[t]

    df_list = [v for k,v in data_wb.items()] 
    return pd.concat(df_list, axis=0)

# Attempt to download the gzipped data catalogue, decompress, and parse out the required information.  
# If we fail to download and extract the gzip and a local copy exists, the script will still run
def fetch_and_parse_catalogue(zip_url, expected_file):
    df = pd.DataFrame()
    datasets = []
    resources = []
    errors = []

    get_and_extract_gzip(zip_url, expected_file)

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