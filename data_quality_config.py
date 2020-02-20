from datetime import date, datetime

# Temporary Data
temp_data_folder = './temp_data/'
remove_temp_data = False

# Configuration
encoding_type = 'utf-8'

supporting_documentation_resource_types = \
    ['guide', 'terminology', 'faq', 'publication', 'plan']

frequency_automatic_point = \
    ['as_needed', 'continual', 'irregular', 'not_planned', 'unknown']

goodtables_supported_file_types = \
    ['csv', 'xls', 'xlsx', 'ods', 'json']

frequency_lookup = {
    'P1D': 2,
    'P0.33W': 9,
    'P0.5W': 9,
    'P1W': 9,
    'P2W': 18,
    'P0.5M': 45,
    'P1M': 45,
    'P2M': 75,
    'P3M': 113,
    'P4M': 150,
    'P6M': 225,
    'P1Y': 456,
    'P2Y': 913,
    'P3Y': 1369,
    'P4Y': 2281
}

snapshot_end_date = datetime(2019, 12, 31, 0, 0, 0)

# Datasets
#catalogue_zip_file = 'http://open.canada.ca/static/od-do-canada.jl.gz'
catalogue_zip_file = temp_data_folder + 'od-do-canada.jl.gz'
catalogue_file = temp_data_folder + 'od-do-canada.jl'

#NOTE: These links (downloads and visits) likely change each time the dataset is generated.  It'll need to be updated after each refresh.
#TODO: Do this properly by leveraging the CKAN API and the GA
#downloads_file = 'https://open.canada.ca/data/dataset/2916fad5-ebcc-4c86-b0f3-4f619b29f412/resource/4ebc050f-6c3c-4dfd-817e-875b2caf3ec6/download/downloads-122019-122019.xls'
downloads_file = temp_data_folder + 'downloads-122019-122019.xls'
#visits_file = 'https://open.canada.ca/data/dataset/2916fad5-ebcc-4c86-b0f3-4f619b29f412/resource/c14ba36b-0af5-4c59-a5fd-26ca6a1ef6db/download/visits-122019-122019.xls'
visits_file = temp_data_folder + 'visits-122019-122019.xls'

nonspatial_file = 'https://search.open.canada.ca/en/od/export/?sort=last_modified_tdt+desc&page=1&search_text=&od-search-portal=Open+Data&od-search-col=Non-Spatial&od-search-jur=Federal'

openness_zip_file = 'https://open.canada.ca/static/openness-details.csv.zip'
openness_file = temp_data_folder + 'openness-details.csv'

user_ratings_file = 'https://open.canada.ca/sites/default/files/dataset-ratings.csv'

# Processed files
#top200_file = 'TopNonSpatialDatasets.csv'
top200_file = 'Top200NonSpatialDatasets.csv'