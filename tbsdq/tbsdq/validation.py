from validate_email import validate_email
from datetime import datetime
from textstat.textstat import textstat
from tbsdq.tbsdq import configuration as dqconfig

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
        if gt_report['tables'][0]['encoding'].startswith('utf-8'):
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

def get_readability_grade(text_to_validate):
    return textstat.flesch_kincaid_grade(text_to_validate)