# System
import os, sys, socket, json
import tempfile
from datetime import datetime
from hashlib import sha1
from pathlib import Path

# 3rd Party
import requests

# Local
import lib.lib


def add(args, config):
    path = '/clients/add/'
    agent_root_dir = os.path.dirname(os.path.dirname(__file__))
    url = lib.lib.get_config_url(config, path)
    api_key = lib.lib.get_config_api_key(config)
    file_path = args[0]
    
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
            'case_sensitive': lib.lib.is_case_sensitive(),
            'mtime': int(st.st_mtime),
            'payload': buf,
        }
    }
    
    req = requests.post(url, data=json.dumps(data))
    resp_body = lib.lib.get_response_body(req)
    obj = json.loads(resp_body)
    lib.lib.check_for_error(obj)
    
    print('Added    {} r1'.format(obj.get('file_path')))


def remove(args, config):
    path = '/clients/remove/'
    agent_root_dir = os.path.dirname(os.path.dirname(__file__))
    url = lib.lib.get_config_url(config, path)
    api_key = lib.lib.get_config_api_key(config)
    file_path = args[0]
    
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
            'case_sensitive': lib.lib.is_case_sensitive(),
            'mtime': int(st.st_mtime),
            'payload': buf,
        }
    }
    
    req = requests.post(url, data=json.dumps(data))
    resp_body = lib.lib.get_response_body(req)
    obj = json.loads(resp_body)
    lib.lib.check_for_error(obj)
    
    print('Removed  {}'.format(obj.get('file_path')))


def disable(args, config):
    pass
