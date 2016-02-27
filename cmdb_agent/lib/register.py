# System
import os, sys, socket, json

# 3rd Party
import requests

# Local
import lib.lib


def register(args, config):
    path = '/clients/register/'
    my_hostname = socket.getfqdn().lower()
    agent_root_dir = os.path.dirname(os.path.dirname(__file__))
    url = lib.lib.get_config_url(config, path)
    req = requests.post(url, data=json.dumps({'fqdn': my_hostname}))
    resp_body = lib.lib.get_response_body(req)
    obj = json.loads(resp_body)
    lib.lib.check_for_error(obj)
    
    print('Host `{}` successfully registered with CMDB!'.format(my_hostname))
    print()
    print('API Key: {}'.format(obj.get('api_key')))
    print()
    print('!!! WARNING: save this API Key in your conifg file: `{}`'.format(
        os.path.join(agent_root_dir, 'config.py')
    ))

def unregister(args, config):
    path = '/clients/unregister/'
    my_hostname = socket.getfqdn().lower()
    api_key = lib.lib.get_config_api_key(config)
    url = lib.lib.get_config_url(config, path)
    req = requests.post(url, data=json.dumps({'api_key': api_key}))
    resp_body = lib.lib.get_response_body(req)
    obj = json.loads(resp_body)
    lib.lib.check_for_error(obj)
    
    print('Host `{}` successfully unregistered with CMDB!'.format(obj.get('fqdn')))
