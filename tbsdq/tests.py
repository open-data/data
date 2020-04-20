from goodtables import validate
import json

def validate_broken_url():
    url = 'https://www.google.com/this/does/not/exist/temp.csv'
    report = validate(url)
    print('**********************************************************************\nVALIDATE BROKEN URL\n**********************************************************************')
    print('Response: {0}'.format(report))
    assert report['tables'][0]['errors'][0]['message'][:3] == '404', 'The expected status was not returned'
    print('**********************************************************************')



validate_broken_url()