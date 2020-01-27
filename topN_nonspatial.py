import pandas as pd

#Faceted Non-Geo OD datasets download link WITH FORMATS - BROKEN
#https://search.open.canada.ca/en/od/export/?sort=last_modified_tdt+desc&page=1&search_text=&od-search-portal=Open+Data&od-search-col=Non-Spatial&od-search-jur=Federal&od-search-format=CSV%7CTXT%7CTAB%7CXML%7CXLSX%7CXLS

#http://open.canada.ca/static/openness-details.csv.zip

#NOTE: These links (downloads and visits) likely change each time the dataset is generated.  It'll need to be updated after each refresh.
#TODO: Do this properly by leveraging the CKAN API and the GA
downloads_file = 'https://open.canada.ca/data/dataset/2916fad5-ebcc-4c86-b0f3-4f619b29f412/resource/4ebc050f-6c3c-4dfd-817e-875b2caf3ec6/download/downloads-122019-122019.xls'
visits_file = 'https://open.canada.ca/data/dataset/2916fad5-ebcc-4c86-b0f3-4f619b29f412/resource/c14ba36b-0af5-4c59-a5fd-26ca6a1ef6db/download/visits-122019-122019.xls'
nonspatial_file = 'https://search.open.canada.ca/en/od/export/?sort=last_modified_tdt+desc&page=1&search_text=&od-search-portal=Open+Data&od-search-col=Non-Spatial&od-search-jur=Federal'
output_file = 'TopNonSpatialDatasets.csv'
output_size = 500
encoding_type = 'utf-8'

def get_analysis_data(f):
    data_wb = pd.read_excel(f, sheet_name=None, skipfooter=1, encoding=encoding_type)
    del data_wb['Summary by departments']
    del data_wb['Top 100 Datasets']

    df_list = [v for k,v in data_wb.items()] 
    return pd.concat(df_list, axis=0)

df_downloads = get_analysis_data(downloads_file)
df_downloads.columns = ['d_id', 'd_title_en', 'd_title_fr', 'd_downloads']

df_visits = get_analysis_data(visits_file)
df_visits.columns = ['v_id', 'v_title_en', 'v_title_fr', 'v_visits']

df_analysis = pd.merge(left=df_downloads, right=df_visits, left_on='d_id', right_on='v_id')
df_analysis = df_analysis[['d_id', 'd_title_en', 'd_downloads', 'v_visits']]

df_nonspatial = pd.read_csv(nonspatial_file, encoding=encoding_type)

df = pd.merge(left=df_nonspatial, right=df_analysis, left_on='id_s', right_on='d_id')
df.columns = ['id', 'owner_org_en', 'owner_org_fr', 'title_en', 'title_fr', 'desc_en', 'desc_fr', 'link_en', 'link_fr', 'id2', 'title_en_2', 'downloads', 'visits']
df[['id', 'owner_org_en', 'title_en', 'desc_en', 'link_en', 'downloads', 'visits']].sort_values(by='downloads', ascending=False).head(output_size).to_csv(output_file, index=None, header=True, encoding=encoding_type)