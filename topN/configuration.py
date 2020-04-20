from datetime import datetime
from tbsdq.tbsdq import configuration as dqconfig

snapshot_end_date = datetime(2019, 12, 31, 0, 0, 0)

# Datasets
# NOTE: This is intentionally locked down to an extract taken at the end of 2019
# TODO: After the initial NAP release when this script is run on a regular schedule, it should pull the catalogue directly from the link below.
#catalogue_zip_file = 'http://open.canada.ca/static/od-do-canada.jl.gz'
catalogue_zip_file = dqconfig.temp_data_folder + 'od-do-canada.jl.gz'
catalogue_file = dqconfig.temp_data_folder + 'od-do-canada.jl'

#NOTE: These links (downloads and visits) likely change each time the dataset is generated.  It'll need to be updated after each refresh.
#TODO: Do this properly by leveraging the CKAN API and the GA
#downloads_file = 'https://open.canada.ca/data/dataset/2916fad5-ebcc-4c86-b0f3-4f619b29f412/resource/4ebc050f-6c3c-4dfd-817e-875b2caf3ec6/download/downloads-122019-122019.xls'
downloads_file = dqconfig.temp_data_folder + 'downloads-122019-122019.xls'
#visits_file = 'https://open.canada.ca/data/dataset/2916fad5-ebcc-4c86-b0f3-4f619b29f412/resource/c14ba36b-0af5-4c59-a5fd-26ca6a1ef6db/download/visits-122019-122019.xls'
visits_file = dqconfig.temp_data_folder + 'visits-122019-122019.xls'

nonspatial_file = 'https://search.open.canada.ca/en/od/export/?sort=last_modified_tdt+desc&page=1&search_text=&od-search-portal=Open+Data&od-search-col=Non-Spatial&od-search-jur=Federal'

openness_zip_file = 'https://open.canada.ca/static/openness-details.csv.zip'
openness_file = dqconfig.temp_data_folder + 'openness-details.csv'

user_ratings_file = 'https://open.canada.ca/sites/default/files/dataset-ratings.csv'

# Processed files
topN_size = 200
topN_file = 'TopN_NonSpatialDatasets.csv'