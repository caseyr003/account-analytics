
'''
Created on July 9, 2018

@author: Casey Ross

Basic Sunburst App for analytics on compute tags

'''

from flask import Flask, render_template, redirect, url_for, request, g
from utils import OCI
import json

app = Flask(__name__)

__version__ = '0.1'

@app.route('/analytics')
def analytics():
    error = None

    config_file="config"
    key_file="api_key.pem"

    with open(config_file) as config:
        account = config.readlines()
    config.closed

    try:
        user = account[1].split('=')[1].rstrip()
        fingerprint = account[2].split('=')[1].rstrip()
        tenancy = account[4].split('=')[1].rstrip()
        region = account[5].split('=')[1].rstrip()
        compartment = account[6].split('=')[1].rstrip()
    except:
        user = ""
        fingerprint = ""
        tenancy = ""
        region = ""
        compartment = ""

    with open(key_file) as data:
        key = data.read()
    data.closed

    api = OCI(tenancy, user, region, fingerprint, key_file, key, compartment, config_file)
    status = api.is_active()
    if status:
        data = api.get_json()
        print(data)
        return render_template('analytics.html', data = data)
    else:
        return render_template('login.html', error=error)

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    print(request)
    if request.method == 'POST':
        user = request.form.get('user_ocid')
        fingerprint = request.form.get('fingerprint')
        key = request.form.get('api_key')
        tenancy = request.form.get('tenancy_ocid')
        region = request.form.get('region')
        compartment = request.form.get('compartment_ocid')
        key_file="api_key.pem"
        config_file="config"
        api = OCI(tenancy, user, region, fingerprint, key_file, key, compartment, config_file)
        status = api.is_active()
        if status:
            data = api.get_json()
            return render_template('analytics.html', data = data)
        else:
            error = "Invalid Account. Please check credentials and try again"
            return render_template('login.html', error=True, err_message=error)

    return render_template('login.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
