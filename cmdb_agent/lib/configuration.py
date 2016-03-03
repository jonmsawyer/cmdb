# System
import os, sys, socket, json
from datetime import datetime

# 3rd Party
import requests

# Local
import lib.lib


def genconfig(args, config):
    agent_root_dir = config.get('AGENT_ROOT_DIR', None)
    if agent_root_dir is None:
        agent_root_dir = os.path.dirname(os.path.dirname(__file__))
    hostname = config.get('HOSTNAME', None)
    port = config.get('PORT', None)
    uri = config.get('URI', None)
    api_key = config.get('API_KEY', None)
    
    agent_root_dir = lib.lib.get_input('What is the root directory of the CMDB agent?', agent_root_dir)
    hostname = lib.lib.get_input('What is the HOSTNAME of the ACS CMDB server?', hostname)
    port = lib.lib.get_input('What is the PORT of the ACS CMDB server?', port)
    uri = lib.lib.get_input('What is the ROOT URI of the ACS CMDB server?', uri)
    api_key = lib.lib.get_input('What is the API KEY of this managed host?', api_key)
    
    print('Agent Root Directory: {}'.format(agent_root_dir))
    print('CMDB Hostname: {}'.format(hostname))
    print('CMDB Port: {}'.format(port))
    print('CMDB URI: {}'.format(uri))
    print('My API Key: {}'.format(api_key))
    
    #req = requests.get(url, params={'api_key': api_key})
    #
    #print('Status code: {}'.format(req.status_code))
    #resp_body = req.content.decode('UTF-8')
    #print('Response body: {}'.format(resp_body))
    #
    #obj = json.loads(resp_body)
    
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
    
    if not '--save-config' in args:
        save_config = lib.lib.get_input('Do you wish to save the configuration (yes/no)?', 'yes')
        if save_config.lower() in ('y', 'yes'):
            save_config = True
        else:
            save_config = False
    else:
        save_config = True
    
    if save_config == True:
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
        
        confirm = lib.lib.get_input('Do you wish to save the configuration to `{}` (yes/no)?'.format(
            os.path.join(agent_root_dir, 'config.py')
        ), 'yes')
        
        if confirm.lower() in ('y', 'yes'):
            print('Saving configuration ...')
            with open(os.path.join(agent_root_dir, 'config.py'), 'w') as fh:
                fh.write(conf)
            print('Done!')
