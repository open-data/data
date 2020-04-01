import pandas as pd
import shutil
import requests, zipfile, gzip, io
import data_quality_config as dqconfig

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