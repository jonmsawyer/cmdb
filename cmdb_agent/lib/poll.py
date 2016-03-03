# System
import os, sys, socket, json, tempfile
from hashlib import sha1
from datetime import datetime

# 3rd Party
import requests

# Local
import lib.lib
from lib.lib import log
from lib.lib import get_input


def sync(args, config):
    path = '/clients/poll/'
    url = lib.lib.get_config_url(config, path)
    api_key = lib.lib.get_config_api_key(config)
    req = requests.get(url, params={'api_key': api_key})
    payload = lib.lib.get_response_body(req)
    payload = json.loads(payload)
    lib.lib.check_for_error(payload)
    
    if payload.get('is_disabled', False) or payload.get('is_blacklisted', False):
        log('Exiting: this host has been disabled.')
        sys.exit(1)
    
    conf_count = payload.get('configuration_count', 0)
    
    if conf_count == 0:
        log('Exiting: there are no configurations to update.')
        sys.exit(0)
    
    configs = payload.get('configurations', [])
    
    if len(configs) != conf_count:
        log('Exiting: configuration count does not match the number of returned configurations.')
        sys.exit(1)
    
    files_to_fetch = []
    files_to_push = []
    files_to_ignore = []
    
    for configuration in configs:
        log(lib.lib.check_local_file(configuration))
        if configuration.get('is_disabled', True):
            log('      D  {} is disabled, skipping...'.format(configuration.get('file_path')))
            continue
        file_path = configuration.get('file_path', '')
        file_found = False
        file_mtime = 0
        try:
            st = os.stat(file_path)
            file_found = True
            file_mtime = int(st.st_mtime)
            file_buf = None
            with open(file_path, 'r') as fh:
                file_buf = fh.read()
            file_sha1_checksum = sha1(file_buf.encode('UTF-8')).hexdigest()
        except FileNotFoundError as e:
            log('      E  {} could not be found, fetching...'.format(file_path))
            file_found = True
            file_mtime = 0
            file_buf = ''
            file_sha1_checksum = sha1(''.encode('UTF-8')).hexdigest()
        
        if file_mtime < configuration.get('mtime', 0):
            log('      F  {} is older than the server, fetching...'.format(file_path))
            files_to_fetch.append(file_path)
            fetch_url = lib.lib.get_config_url(config, '/clients/fetch/')
            fetch(fetch_url, api_key, file_path, configuration.get('mtime', 0))
        elif file_mtime == configuration.get('mtime', 0):
            log('      I  {} is same age as the server, ignoring...'.format(file_path))
            files_to_ignore.append(file_path)
        elif file_mtime > configuration.get('mtime', 0):
            log('      P  {} is newer than the server, pushing...'.format(file_path))
            push_url = fetch_url = lib.lib.get_config_url(config, '/clients/push/')
            push(push_url, api_key, file_path)
            files_to_push.append(file_path)


def fetch(url, api_key, file_path, mtime):
    #log('Fetch: {}, {}, {}, {}'.format(url, api_key, file_path, mtime))
    #log('Fetching `{}` from server...'.format(file_path))
    req = requests.get(url, params={'api_key': api_key, 'file_path': file_path})
    resp_body = lib.lib.get_response_body(req)
    payload = json.loads(resp_body)
    lib.lib.check_for_error(payload)
    #log('Payload: {}'.format(payload))
    with open(file_path, 'w') as fh:
        fh.write(payload.get('content'))
    os.utime(file_path, (mtime, mtime))
    
    print(lib.lib.check_local_file(payload))


def push(url, api_key, file_path):
    #log('Push: {}, {}, {}'.format(url, api_key, file_path))
    #log('Pushing `{}` to server...'.format(file_path))
    
    try:
        mtime = os.stat(file_path).st_mtime
    except:
        log('Push abort, could not stat `{}`'.format(file_path))
        return False
    
    buf = ''
    with open(file_path, 'r') as fh:
        buf = fh.read()
    
    sha1_checksum = sha1(buf.encode('UTF-8')).hexdigest()
    
    data = {
        'api_key': api_key,
        'file_path': file_path,
        'mtime': int(mtime),
        'content': buf,
        'sha1_checksum': sha1_checksum,
        'case_sensitive': lib.lib.is_case_sensitive(),
    }
    
    req = requests.post(url, data=json.dumps(data))
    resp_body = lib.lib.get_response_body(req)
    payload = json.loads(resp_body)
    lib.lib.check_for_error(payload)
    
    #log('Payload: {}'.format(json.dumps(payload, indent=4)))
    print(lib.lib.check_local_file(payload))
