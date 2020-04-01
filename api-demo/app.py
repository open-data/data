from flask import Flask, render_template
from flask_restful import Resource, Api, reqparse
from textstat.textstat import textstat
from validate_email import validate_email
import goodtables as gt

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
    readability_score = textstat.flesch_kincaid_grade(form_object['description'])
    valid_readability = True if readability_score <= 8 else False
    other_dept_using_tbs_open = False
    is_email_valid = False
    
    if form_object['department'].startswith("Treasury Board"):
        is_email_valid = validate_email(form_object['maintainer_email'])
    else:
        if form_object['maintainer_email'].split('@')[-1].lower() == "tbs-sct.gc.ca":
            is_email_valid = False
            other_dept_using_tbs_open = True
        else:
            is_email_valid = validate_email(form_object['maintainer_email'])

    user_file_type = form_object['file_type'].lower();

    gt_report = gt.validate(form_object['file_link'])

    try:
        link_return_status = int(gt_report['tables'][0]['errors'][0]['message'][:3])
    except:
        link_return_status = 200

    link_encoding = gt_report['tables'][0]['encoding']
    link_file_validity = gt_report['tables'][0]['valid']
    link_error_count = gt_report['tables'][0]['error-count']
    link_file_type = gt_report['tables'][0]['format'].lower()
    link_error_details = gt_report['tables'][0]['errors']
    valid_url = True if int(link_return_status) < 400 else False
    valid_encoding = True if link_encoding == 'utf-8' else False
    valid_format = link_file_validity
    url_type = form_object['file_link'].split('.')[-1].lower()

    valid_file_type = True if url_type == user_file_type or user_file_type == link_file_type else False

    return {
        'readability_score': readability_score,
        'valid_readability': valid_readability,
        'is_email_valid': is_email_valid,
        'other_dept_using_tbs_open': other_dept_using_tbs_open,
        'link_http_status': link_return_status,
        'valid_url': valid_url,
        'link_encoding': link_encoding,
        'valid_encoding': valid_encoding,
        'link_file_type': link_file_type,
        'user_file_type': user_file_type,
        'valid_file_type': valid_file_type,
        'valid_format': valid_format,
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