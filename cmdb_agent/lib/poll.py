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
    
    for configuration in configs:
        file_path = configuration.get('file_path')
        remote_file = lib.lib.RemoteConfigFile(file_path, config)
        remote_file.resolve()
        local_file = lib.lib.LocalConfigFile(file_path, config)
        local_file.resolve()
        print('Remote config: {}'.format(remote_file.config))
        print('Local config: {}'.format(local_file.config))
        log(lib.lib.check_local_file(configuration))
        
        if remote_file.config.get('is_disabled') == True:
            #if configuration.get('is_disabled', True):
            log('      D    `- {} is disabled, skipping...'.format(configuration.get('file_path')))
            continue
        
        if local_file.is_file_not_found == True:
            log('      E    `- {} could not be found, fetching...'.format(file_path))
        if local_file < remote_file:
            log('      F    `- {} is older than the server, fetching...'.format(file_path))
            fetch_url = lib.lib.get_config_url(config, '/clients/fetch/')
            fetch(fetch_url, api_key, file_path, configuration.get('mtime', 0))
        elif local_file == remote_file:
            log('      I    `- {} is same age as the server, ignoring...'.format(file_path))
        elif local_file > remote_file:
            log('      P         `- {} is newer than the server, pushing...'.format(file_path))
            push_url = fetch_url = lib.lib.get_config_url(config, '/clients/push/')
            push(push_url, api_key, file_path)

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
