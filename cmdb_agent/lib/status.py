# System
import os, sys, socket, json

# 3rd Party
import requests

# Local
import lib.lib


def info(args, config):
    path = '/clients/info/'
    uri = lib.lib.get_config_uri(config)
    url = lib.lib.get_config_url(config, path)
    api_key = lib.lib.get_config_api_key(config)
    req = requests.get(url, params={'api_key': api_key})
    resp_body = lib.lib.get_response_body(req)
    obj = json.loads(resp_body)
    lib.lib.check_for_error(obj)
    
    print('CMDB URI:                {}'.format(uri))
    print('Client name:             {}'.format(obj.get('name', '')))
    print('Client registered on:    {}'.format(obj.get('date_created')))
    print('Client API Key:          {}'.format(obj.get('api_key', '')))
    print('Client disabled?         {}'.format(obj.get('is_disabled')))
    print('Client blacklisted?      {}'.format(obj.get('is_blacklisted')))
    print('Configurations Tracking: {}'.format(obj.get('configurations_tracking')))


def status(args, config):
    path = '/clients/status/'
    url = lib.lib.get_config_url(config, path)
    api_key = lib.lib.get_config_api_key(config)
    req = requests.get(url, params={'api_key': api_key})
    resp_body = lib.lib.get_response_body(req)
    obj = json.loads(resp_body)
    lib.lib.check_for_error(obj)
    
    for config in obj.get('configurations'):
        print(lib.lib.check_local_file(config))
    
    #print('Response body: {}'.format(json.dumps(obj, indent=4)))
