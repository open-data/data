import importlib
from flask import Flask, render_template, request
from flask_restful import Resource, Api, reqparse
import pandas as pd
from tbsdq import data_quality as dq

#Resource = importlib.__import__("flask_restful.resource")
#Api = importlib.__import__("flask_restful.Api")
#reqparse = importlib.__import__("flask_restful.reqparse")


#Resource = importlib.__import__("Flask-RESTful.Resource")
#Api = importlib.__import__("Flask-RESTful.Api")
#reqparse = importlib.__import__("Flask-RESTful.reqparse")
app = Flask(__name__)
api = Api(app)

@app.route('/', methods=['GET', 'POST'])
def index():
# Check if there's a JSON object with form data in POST.  If not, create an empty object and render the template to the browser
    try:
        data_json = request.get_json()
        data = {
            'description': data_json['description'],
            'department': data_json['department'],
            'email': data_json['email'],
            'file_type': data_json['file_type'],
            'file_link': data_json['file_link']
        }
    except:
        data = {
            'description': '',
            'department': '',
            'email': '',
            'file_type': '',
            'file_link': ''
        }
    return render_template('index.html', data=data)

# **************************************************************
# Data Quality Validation
# **************************************************************

parser = reqparse.RequestParser()

def data_quality_validation(form_object):
    # Create the single_record dictionary to pass into the tbsdq module for validation
    single_record = {
        'description_en': form_object['description'],
        'description_fr': form_object['description'],
        'owner_org': form_object['department'],
        'maintainer_email': form_object['maintainer_email'],
        'url': form_object['file_link'],
        'source_format': form_object['file_type']
    }
    # Validate the dictionary and capture the returned pandas dataframe
    df_quality = dq.dq_validate(single_record, 'single')
    # Map to the JSON report returned from goodtables contained within the dataframe
    gt_report = df_quality['goodtables_report'][0]

    # Check for departments other than TBS using the open@tbs email address
    other_dept_using_tbs_open = False
    if form_object['department'].startswith("Treasury Board") and form_object['maintainer_email'].split('@')[-1].lower() == "tbs-sct.gc.ca":
        other_dept_using_tbs_open = True

    # Extract the specific report values we need to return to the user
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

# **************************************************************
# Form Handling
# **************************************************************

user_submission = {
    "description": "",
    "department": "",
    "maintainer_email": "",
    "file_type": "",
    "file_link": ""
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

api.add_resource(FormInput, '/validate/')

if __name__ == '__main__':
    app.run(debug=True)