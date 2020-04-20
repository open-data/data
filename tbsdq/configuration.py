from datetime import date, datetime

# Temporary Data
temp_data_folder = './temp_data/'
remove_temp_data = False

# Configuration
encoding_type = 'utf-8'

supporting_documentation_resource_types = \
    ['guide', 'terminology', 'faq', 'publication', 'plan', 'specification']

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

registry_formats = [
    'zip',
    'csv',
    'xls',
    'json',
    'xml',
    'txt',
    'ods',
    'sql'
]

bad_http_status = [
    '404',
    '500',
    '503'
]

readability_pass_en = 8
readability_pass_fr = 8