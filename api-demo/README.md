# In-line Data Quality Validation Demo

This demo delivers data quality validation in the browser using a simple HTML form and a Python Flask API.

## Installation
`cd <this folder>`

`virtualenv venv`

`venv/Scripts/activate`

`pip install -r requirements.txt`

`python app.py`


## View the Local Demo
Open your browser and go to http://127.0.0.1:5000

## Post to pre-fill form fields
If you would like to auto-populate the form with values entered from another source, you can submit a POST to the root of this site with the following JSON template:

```
{
    "description": "The description of the package",
    "department": "The owning department / org",
    "email": "The maintainer email address for the package",
    "file_type": "The user-specified file type (e.g. CSV, XML, JSON)"
    "file_link": "The full URL to the actual data file to validate"
}
```

