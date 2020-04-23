from flask import Flask, render_template
from flask_restful import Resource, Api, reqparse
import pandas as pd
from tbsdq import data_quality as dq

app = Flask(__name__)
api = Api(app)

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/validate')
def validate_form():
    return '{"status": "success"}'

# **************************************************************

user_submission = {
    "description": "Some description.",
    "department": "Treasury Board Secretariat of Canada",
    "maintainer_email": "open@tbs-sct.gc.ca"
}

parser = reqparse.RequestParser()

def data_quality_validation(form_object):
    single_record = {
        'description_en': form_object['description'],
        'description_fr': form_object['description'],
        'owner_org': form_object['department'],
        'maintainer_email': form_object['maintainer_email'],
        'url': form_object['file_link'],
        'source_format': form_object['file_type']
    }
    df_quality = dq.dq_validate(single_record, 'single')
    gt_report = df_quality['goodtables_report'][0]

    other_dept_using_tbs_open = False
    if form_object['department'].startswith("Treasury Board") and form_object['maintainer_email'].split('@')[-1].lower() == "tbs-sct.gc.ca":
        other_dept_using_tbs_open = True

    link_encoding = gt_report['tables'][0]['encoding']
    link_file_validity = gt_report['tables'][0]['valid']
    link_error_count = gt_report['tables'][0]['error-count']
    link_file_type = gt_report['tables'][0]['format'].lower()
    link_error_details = gt_report['tables'][0]['errors']

    return {
        'readability_score': df_quality['readability_grade_en'][0],
        'valid_readability': bool(df_quality['valid_readability_en'][0]),
        'is_email_valid': bool(df_quality['valid_maintainer_email'][0]),
        'other_dept_using_tbs_open': other_dept_using_tbs_open,
        'valid_url': bool(df_quality['valid_url'][0]),
        'link_encoding': link_encoding,
        'valid_encoding': bool(df_quality['valid_encoding'][0]),
        'link_file_type': link_file_type,
        'user_file_type': form_object['file_type'].lower(),
        'valid_file_type': bool(df_quality['valid_file_type'][0]),
        'valid_format': bool(df_quality['valid_format'][0]),
        'error_count': link_error_count,
        'error_details': link_error_details,
    }
    
class FormInput(Resource):
    def get(self):
        return user_submission
    def post(self):
        parser.add_argument("description")
        parser.add_argument("department")
        parser.add_argument("maintainer_email")
        parser.add_argument("file_type")
        parser.add_argument("file_link")
        args = parser.parse_args()
        user_submission = {
            "description": args['description'],
            "department": args['department'],
            "maintainer_email": args['maintainer_email'],
            "file_type": args['file_type'],
            "file_link": args['file_link'],
        }
        return data_quality_validation(user_submission), 201

api.add_resource(FormInput, '/samplevalidate/')

if __name__ == '__main__':
    app.run(debug=True)