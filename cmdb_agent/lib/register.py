import os, sys
import requests
import socket
import json
from datetime import date, time, datetime, timedelta

from lib.lib import get_input


def register(args, config):
    api_key = None
    hostname = None
    port = None
    uri = None
    path = '/clients/register/'
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
    
    my_hostname = socket.getfqdn().lower()
    
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
    print('My Hostname: {}'.format(my_hostname))
    
    req = requests.post(url, data=json.dumps({'fqdn': my_hostname}))
    
    print('Status code: {}'.format(req.status_code))
    resp_body = req.content.decode('UTF-8')
    if req.status_code != 200:
        with open(r'c:\error.html', 'w') as fh:
            fh.write(resp_body)
        print('There was an error, check c:\error.html.')
        sys.exit(1)
    else:
        print('Response body: {}'.format(resp_body))
    obj = json.loads(resp_body)
    
    buf = '''# File: config.py
# This is an automagically generated file. It was created by `agent.py` on
# {datetime}.

AGENT_ROOT_DIR = r'{agent_root_dir}'
HOSTNAME = '{hostname}'
PORT = {port}
URI = '{uri}'
API_KEY = '{api_key}'
POLL_LOG_FILE = 'poll.log'

# End config
'''
    conf = None
    
    if 'api_key' in obj and '--save-config' in args:
        conf = buf.format(
            hostname=hostname,
            port=port,
            uri=uri,
            api_key=obj.get('api_key'),
            datetime=datetime.now().isoformat(' '),
            agent_root_dir=agent_root_dir
        )
        print('Config:')
        print('=======')
        print(conf)
    elif '--save-config' in args:
        conf = buf.format(
            hostname=hostname,
            port=port,
            uri=uri,
            api_key=api_key,
            datetime=datetime.now().isoformat(' '),
            agent_root_dir=agent_root_dir
        )
        print('Config:')
        print('=======')
        print(conf)
    
    if '--save-config' in args:
        confirm = get_input('Do you wish to save the configuration to `{}` (yes/no)?'.format(
            os.path.join(agent_root_dir, 'config.py')
        ))
        
        if confirm.lower() in ('y', 'yes'):
            print('Saving configuration ...')
            with open(os.path.join(agent_root_dir, 'config.py'), 'w') as fh:
                fh.write(conf)
            print('Done!')


def unregister(args, config):
    api_key = None
    hostname = None
    port = None
    uri = None
    path = '/clients/unregister/'
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
    
    my_hostname = socket.getfqdn().lower()
    
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
    print('My Hostname: {}'.format(my_hostname))
    
    req = requests.post(url, data=json.dumps({'fqdn': my_hostname}))
    
    print('Status code: {}'.format(req.status_code))
    resp_body = req.content.decode('UTF-8')
    if req.status_code != 200:
        with open(r'c:\error.html', 'w') as fh:
            fh.write(resp_body)
            print('There was an error, check c:\error.html.')
    else:
        print('Response body: {}'.format(resp_body))
