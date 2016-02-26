import os, sys, tempfile
import requests
import socket
import json
from hashlib import sha1
from datetime import date, time, datetime, timedelta

log_file_path = None
agent_config = None


def case_sensitive():
    cs = True
    temp_handle, temp_path = tempfile.mkstemp()
    if os.path.exists(temp_path.upper()):
        cs = False
    os.close(temp_handle)
    os.unlink(temp_path)
    return cs

CASE_SENSITIVE = case_sensitive()


def init_log_file(config):
    global log_file_path
    
    if log_file_path is None:
        if hasattr(config, 'POLL_LOG_FILE') and hasattr(config, 'AGENT_ROOT_DIR'):
            log_file_path = os.path.join(getattr(config, 'AGENT_ROOT_DIR'), getattr(config, 'POLL_LOG_FILE'))


def log(msg, level='INFO', stdout=True):
    global agent_config
    global log_file_path
    name = 'POLL'
    now = datetime.now().isoformat(' ')
    
    if log_file_path is None and agent_config is not None:
        init_log_file(agent_config)
    else:
        log_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'poll.log')
    
    with open(log_file_path, 'a') as fh:
        log_msg = '{name} | {now} | {level} | {msg}\r\n'.format(
            name=name, now=now, level=level, msg=msg)
        fh.write(log_msg)
        if stdout == True:
            print(log_msg)


def get_input(msg):
    if not msg.endswith(' '):
        msg += ' '
    key_in = None
    while key_in is None:
        key_in = input(msg)
    return key_in


def poll(args, config):
    global agent_config
    agent_config = config
    
    try:
        hostname = config.HOSTNAME
        port = config.PORT
        uri = config.URI
        path = '/clients/poll/'
        api_key = config.API_KEY
    except Exception as e:
        log('Could not get configuration details:')
        log(str(e))
    
    url = 'http://{hostname}:{port}{uri}{path}'.format(
            hostname=hostname,
            port=port,
            uri=uri,
            path=path)
    
    log('Polling {} for CMDB updates...'.format(url))
    r = requests.get(url, params={'api_key': api_key})
    log('Polling status code: {}'.format(r.status_code))
    if r.status_code != 200:
        with open(r'c:\error.html', 'w') as fh:
            fh.write(r.text)
        log('An error occurred. See c:\error.html.')
        sys.exit(1)
    payload = json.loads(r.content.decode('UTF-8'))
    log('Payload: {}'.format(json.dumps(payload, indent=4)))
    
    if payload.get('is_disabled', True):
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
    
    for config in configs:
        if config.get('is_disabled', True):
            log('`{}` is disabled, skipping...'.format(config.get('file_path', '<no_file_path_given>')))
            continue
        file_path = config.get('file_path', '')
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
            log('Could not find local file `{}`, fetching...'.format(file_path))
            file_found = True
            file_mtime = 0
            file_buf = ''
            file_sha1_checksum = sha1(''.encode('UTF-8')).hexdigest()
        
        if file_mtime < config.get('mtime', 0):
            log('`{}` is older than the server, fetching...'.format(file_path))
            files_to_fetch.append(file_path)
            fetch_url = 'http://{hostname}:{port}{uri}/clients/fetch/'.format(
                hostname=hostname,
                port=port,
                uri=uri)
            checksum = fetch(fetch_url, api_key, file_path, config.get('mtime', 0))
            log('Returned checksum: {}'.format(checksum))
            if checksum == False:
                log('Failed to fetch `{}`, fetch returned False.'.format(file_path))
            if checksum == config.get('sha1_checksum', ''):
                log('Checksums MATCH!')
            else:
                log('Checksums DO NOT MATCH! Why?')
        elif file_mtime == config.get('mtime', 0):
            log('`{}` is same age as the server, ignoring...'.format(file_path))
            files_to_ignore.append(file_path)
        elif file_mtime > config.get('mtime', 0):
            log('`{}` is newer than the server, pushing...'.format(file_path))
            push_url = fetch_url = 'http://{hostname}:{port}{uri}/clients/push/'.format(
                hostname=hostname,
                port=port,
                uri=uri)
            push(push_url, api_key, file_path)
            files_to_push.append(file_path)


def fetch(url, api_key, file_path, mtime):
    log('Fetch: {}, {}, {}, {}'.format(url, api_key, file_path, mtime))
    log('Fetching `{}` from server...'.format(file_path))
    req = requests.get(url, params={'api_key': api_key, 'file_path': file_path})
    if req.status_code == 200:
        payload = json.loads(req.text)
        log('Payload: {}'.format(json.dumps(payload, indent=4)))
        with open(file_path, 'w') as fh:
            fh.write(payload.get('content'))
        os.utime(file_path, (mtime, mtime))
        buf = ''
        with open(file_path, 'r') as fh:
            buf = fh.read()
        chksum = sha1(buf.encode('UTF-8')).hexdigest()
        log('Checksum of file on disk: {}'.format(chksum))
        return chksum
    else:
        log('Could not fetch `{}` from the server, the returned status code was `{}`'.format(file_path, req.status_code))
        return False


def push(url, api_key, file_path):
    log('Push: {}, {}, {}'.format(url, api_key, file_path))
    log('Pushing `{}` to server...'.format(file_path))
    
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
        'case_sensitive': CASE_SENSITIVE, 
    }
    #print("The data...: {}".format(json.dumps(data)))
    req = requests.post(url, data=json.dumps(data))
    if req.status_code == 200:
        payload = json.loads(req.text)
        log('Payload: {}'.format(json.dumps(payload, indent=4)))
        return True
    else:
        log('Could not push `{}` to the server, the returned status code was `{}`'.format(file_path, req.status_code))
        with open(r'c:\error.html', 'w') as fh:
            fh.write(req.text)
        return False
