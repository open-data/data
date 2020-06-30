
import pandas as pd
from topN import build_dataset as topnbuild
from topN import configuration as topnconfig
from tbsdq import configuration as dqconfig

# Load the Top 200 Non Spatial file.  Exit with an error if we can't find or build it. 
def get_top_N_non_spatial():
    try:
        df = pd.read_csv(topnconfig.topN_file, encoding=dqconfig.encoding_type)
        return df[['id','openness_rating','user_rating_score','user_rating_count']]
    except:
        print('Top N Dataset not found.  Attempting to build it now.')
        try:
            topnbuild.build_top_N_dataset()
            df = pd.read_csv(topnconfig.topN_file, encoding=dqconfig.encoding_type)
            return df[['id','openness_rating','user_rating_score','user_rating_count']]
        except:
            raise