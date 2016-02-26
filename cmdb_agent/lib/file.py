import os, sys
import requests
import socket
import json
from datetime import date, time, datetime, timedelta
import tempfile
from hashlib import sha1
from pathlib import Path


def get_input(msg):
    key_in = None
    while key_in == None:
        key_in = input(msg+' ')
    return key_in

def case_sensitive():
    cs = True
    temp_handle, temp_path = tempfile.mkstemp()
    if os.path.exists(temp_path.upper()):
        cs = False
    os.close(temp_handle)
    os.unlink(temp_path)
    return cs

CASE_SENSITIVE = case_sensitive()

def add(args, config):
    api_key = None
    hostname = None
    port = None
    uri = None
    path = '/clients/add/'
    agent_root_dir = os.path.dirname(os.path.dirname(__file__))
    
    if config:
        if hasattr(config, 'HOSTNAME'):
            hostname = getattr(config, 'HOSTNAME')
        if hasattr(config, 'PORT'):
            port = getattr(config, 'PORT')
        if hasattr(config, 'URI'):
            uri = getattr(config, 'URI')
        if hasattr(config, 'API_KEY'):
            api_key = getattr(config, 'API_KEY')
    
    if not hostname:
        hostname = get_input('What is the HOSTNAME of the ACS CMDB server?')
    
    if not port:
        port = get_input('What is the PORT of the ACS CMDB server?')
    
    if not uri:
        uri = get_input('What is the ROOT URI of the ACS CMDB server?')
    
    if not api_key:
        api_key = get_input('What is the API KEY of this managed host?')
    
    url = 'http://{hostname}:{port}{uri}{path}'.format(
        hostname=hostname,
        port=port,
        uri=uri,
        path=path
    )
    
    print('Agent Root Directory: {}'.format(agent_root_dir))
    print('CMDB Hostname: {}'.format(hostname))
    print('CMDB Port: {}'.format(port))
    print('CMDB URI: {}'.format(uri))
    print('CMDB Path: {}'.format(path))
    print('CMDB URL: {}'.format(url))
    print('My API Key: {}'.format(api_key))
    
    if len(args) > 2:
        file_path = args[2]
    else:
        print('Missing FILE parameter for command `add`.')
        sys.exit(1)
    
    try:
        file_path = str(Path(file_path).resolve())
        st = os.stat(file_path)
    except:
        print('Missing file `{}` on filesystem, cannot add to CMDB.'.format(file_path))
        sys.exit(1)
    
    try:
        buf = None
        with open(file_path, 'r') as fh:
            buf = fh.read()
    except UnicodeDecodeError as e:
        print('File `{}` is not a text file, aborting.'.format(file_path))
        sys.exit(1)
    
    try:
        buf.encode('UTF-8')
    except:
        print('File `{}` is not a text file, aborting.'.format(file_path))
        sys.exit(1)
    
    data = {
        'api_key': api_key,
        'type': 'configuration',
        'configuration': {
            'file_path': file_path,
            'case_sensitive': CASE_SENSITIVE,
            'mtime': int(st.st_mtime),
            'payload': buf,
        }
    }
    
    req = requests.post(url, data=json.dumps(data))
    
    print('Status code: {}'.format(req.status_code))
    resp_body = req.content.decode('UTF-8')
    if req.status_code != 200:
        with open(r'c:\error.html', 'w') as fh:
            fh.write(resp_body)
            print('An error occurred, check c:\error.html.')
    else:
        print('Response body: {}'.format(json.dumps(json.loads(resp_body), indent=4)))


def remove(args, config):
    api_key = None
    hostname = None
    port = None
    uri = None
    path = '/clients/remove/'
    agent_root_dir = os.path.dirname(os.path.dirname(__file__))
    
    if config:
        if hasattr(config, 'HOSTNAME'):
            hostname = getattr(config, 'HOSTNAME')
        if hasattr(config, 'PORT'):
            port = getattr(config, 'PORT')
        if hasattr(config, 'URI'):
            uri = getattr(config, 'URI')
        if hasattr(config, 'API_KEY'):
            api_key = getattr(config, 'API_KEY')
    
    if not hostname:
        hostname = get_input('What is the HOSTNAME of the ACS CMDB server?')
    
    if not port:
        port = get_input('What is the PORT of the ACS CMDB server?')
    
    if not uri:
        uri = get_input('What is the ROOT URI of the ACS CMDB server?')
    
    if not api_key:
        api_key = get_input('What is the API KEY of this managed host?')
    
    url = 'http://{hostname}:{port}{uri}{path}'.format(
        hostname=hostname,
        port=port,
        uri=uri,
        path=path
    )
    
    print('Agent Root Directory: {}'.format(agent_root_dir))
    print('CMDB Hostname: {}'.format(hostname))
    print('CMDB Port: {}'.format(port))
    print('CMDB URI: {}'.format(uri))
    print('CMDB Path: {}'.format(path))
    print('CMDB URL: {}'.format(url))
    print('My API Key: {}'.format(api_key))
    
    if len(args) > 2:
        file_path = args[2]
    else:
        print('Missing FILE parameter for command `remove`.')
        sys.exit(1)
    
    try:
        file_path = str(Path(file_path).resolve())
        st = os.stat(file_path)
    except:
        print('Missing file `{}` on filesystem, cannot add to CMDB.'.format(file_path))
        sys.exit(1)
    
    try:
        buf = None
        with open(file_path, 'r') as fh:
            buf = fh.read()
    except UnicodeDecodeError as e:
        print('File `{}` is not a text file, aborting.'.format(file_path))
        sys.exit(1)
    
    try:
        buf.encode('UTF-8')
    except:
        print('File `{}` is not a text file, aborting.'.format(file_path))
        sys.exit(1)
    
    data = {
        'api_key': api_key,
        'type': 'configuration',
        'configuration': {
            'file_path': file_path,
            'case_sensitive': CASE_SENSITIVE,
            'mtime': int(st.st_mtime),
            'payload': buf,
        }
    }
    
    req = requests.post(url, data=json.dumps(data))
    
    print('Status code: {}'.format(req.status_code))
    resp_body = req.content.decode('UTF-8')
    if req.status_code != 200:
        with open(r'c:\error.html', 'w') as fh:
            fh.write(resp_body)
            print('An error occurred, check c:\error.html.')
    else:
        print('Response body: {}'.format(json.dumps(json.loads(resp_body), indent=4)))


def disable(args, config):
    pass
