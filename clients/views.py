import json

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from clients.models import Client, Configuration, ConfigurationFile
from clients.models import ClientException

from cmdb_agent.lib import lib

def error_msg(msg):
    return HttpResponse(json.dumps({'error': msg}), content_type='application/json')

def debug_msg(msg):
    return HttpResponse(json.dumps({'debug': msg}), content_type='application/json')

def status_msg(name, date_created, is_disabled, is_blacklisted, api_key=''):
    msg_dict = {
        'name': name,
        'date_created': str(date_created),
        'is_disabled': is_disabled,
        'is_blacklisted': is_blacklisted,
    }
    if len(api_key) == 40:
        msg_dict.update({'api_key': api_key})
    
    return HttpResponse(json.dumps(msg_dict), content_type='application/json')

def config_status_msg(config_status):
    return HttpResponse(json.dumps(config_status), content_type='application/json')

def unregister_msg(name, is_disabled):
    return HttpResponse(json.dumps({'fqdn': name, 'is_disabled': is_disabled}), content_type='application/json')

def configuration_added_msg(details):
    return HttpResponse(json.dumps(details), content_type='application/json')


def poll_msg(details):
    return HttpResponse(json.dumps(details), content_type='application/json')

def fetch_msg(details):
    return HttpResponse(json.dumps(details), content_type='application/json')


@csrf_exempt
def register(request):
    if request.method == 'POST':
        obj = json.loads(request.body.decode('UTF-8'))
        try:
            fqdn = lib.require_key(obj, 'fqdn')
        except Exception as e:
            return error_msg(str(e))
        try:
            client = Client.new_client(fqdn)
            if not client:
                return error_msg('Client `{}` is already registered.'.format(fqdn))
        except ClientException as e:
            return error_msg(str(e))
        
        return status_msg(fqdn, client.date_created, client.is_disabled, client.is_blacklisted, client.api_key)
    else:
        return error_msg('Invalid method.')


@csrf_exempt
def unregister(request):
    if request.method == 'POST':
        obj = json.loads(request.body.decode('UTF-8'))
        try:
            api_key = lib.require_key(obj, 'api_key')
        except Exception as e:
            return error_msg(str(e))
        try:
            client = Client.disable_client(api_key)
            return unregister_msg(client.client_name, client.is_disabled)
        except Exception as e:
            return error_msg(str(e))
    else:
        return error_msg('Invalid method.')


def status(request):
    if request.method == 'GET':
        api_key = request.GET.get('api_key', '')
        if len(api_key) != 40:
            return error_msg('Invalid `api_key`.')
        
        try:
            client = Client.objects.get(api_key=api_key)
            return status_msg(client.client_name, client.date_created, client.is_disabled, client.is_blacklisted)
        except:
            return error_msg('Client for `api_key` doesn\'t exist.')


def config_status(request):
    if request.method == 'GET':
        api_key = request.GET.get('api_key', '')
        if len(api_key) != 40:
            return error_msg('Invalid `api_key`.')
        
        try:
            config_status = Client.get_config_status(api_key)
            return config_status_msg(config_status)
        except:
            raise
            return error_msg('Client for `api_key` doesn\'t exist.')


@csrf_exempt
def add(request):
    if request.method == 'POST':
        obj = json.loads(request.body.decode('UTF-8'))
        if 'api_key' not in obj:
            return error_msg('Could not find `api_key` key in object.')
        try:
            client = Client.get_by_api_key(obj.get('api_key'))
        except:
            return error_msg('Invalid API Key.')
        
        if client.is_disabled:
            return error_msg('Client for `api_key` is currently disabled.')
        
        if 'type' not in obj:
            return error_msg('Could not find `type` key in object.')
        
        add_type = obj.get('type', '')
        if add_type == 'configuration':
            if add_type not in obj:
                return error_msg('Could not find `{}` key in object.'.format(add_type))
            
            # Get `file_path`
            if 'file_path' not in obj.get('configuration'):
                return error_msg('Could not find `file_path` key in object.configuration.')
            else:
                try:
                    file_path = str(obj.get('configuration').get('file_path'))
                except:
                    return error_msg('`file_path` must be a string.')
            
            # Get `mtime`
            if 'mtime' not in obj.get('configuration'):
                return error_msg('Could not find `mtime` key in object.configuration.')
            else:
                try:
                    mtime = int(str(obj.get('configuration').get('mtime')))
                except:
                    return error_msg('`mtime` must be a numerical string or an integer.')
            
            # Get `payload`
            if 'payload' not in obj.get('configuration'):
                return error_msg('Could not find `payload` key in object.configuration.')
            else:
                try:
                    payload = obj.get('configuration').get('payload')
                except:
                    return error_msg('`payload` must be a string.')
            
            # Get `case_sensitive`
            if 'case_sensitive' not in obj.get('configuration'):
                return error_msg('Could not find `case_sensitive` key in object.configuration.')
            else:
                try:
                    case_sensitive = bool(obj.get('configuration').get('case_sensitive'))
                except:
                    return error_msg('`case_sensitive` must be boolean.')
            
            details = {
                'file_path': file_path,
                'mtime': mtime,
                'case_sensitive': case_sensitive,
                'payload': payload,
            }
            
            try:
                Configuration.add(client, **details)
            except Exception as e:
                return error_msg(str(e))
            
            return configuration_added_msg(details)
        else:
            return error_msg('Could not understand the type: `{}`.'.format(obj.get('type')))
    else:
        return error_msg('Invalid method.')


@csrf_exempt
def remove(request):
    if request.method == 'POST':
        obj = json.loads(request.body.decode('UTF-8'))
        if 'api_key' not in obj:
            return error_msg('Could not find `api_key` key in object.')
        try:
            client = Client.get_by_api_key(obj.get('api_key'))
        except:
            return error_msg('Invalid API Key.')
        
        if client.is_disabled:
            return error_msg('Client for `api_key` is currently disabled.')
        
        if 'type' not in obj:
            return error_msg('Could not find `type` key in object.')
        
        add_type = obj.get('type', '')
        if add_type == 'configuration':
            if add_type not in obj:
                return error_msg('Could not find `{}` key in object.'.format(add_type))
            
            # Get `file_path`
            if 'file_path' not in obj.get('configuration'):
                return error_msg('Could not find `file_path` key in object.configuration.')
            else:
                try:
                    file_path = str(obj.get('configuration').get('file_path'))
                except:
                    return error_msg('`file_path` must be a string.')
            
            # Get `mtime`
            if 'mtime' not in obj.get('configuration'):
                return error_msg('Could not find `mtime` key in object.configuration.')
            else:
                try:
                    mtime = int(str(obj.get('configuration').get('mtime')))
                except:
                    return error_msg('`mtime` must be a numerical string or an integer.')
            
            # Get `payload`
            if 'payload' not in obj.get('configuration'):
                return error_msg('Could not find `payload` key in object.configuration.')
            else:
                try:
                    payload = obj.get('configuration').get('payload')
                except:
                    return error_msg('`payload` must be a string.')
            
            # Get `case_sensitive`
            if 'case_sensitive' not in obj.get('configuration'):
                return error_msg('Could not find `case_sensitive` key in object.configuration.')
            else:
                try:
                    case_sensitive = bool(obj.get('configuration').get('case_sensitive'))
                except:
                    return error_msg('`case_sensitive` must be boolean.')
            
            details = {
                'file_path': file_path,
                'mtime': mtime,
                'case_sensitive': case_sensitive,
                'payload': payload,
            }
            
            try:
                Configuration.remove(client, **details)
            except Exception as e:
                return error_msg(str(e))
            
            return configuration_added_msg(details)
        else:
            return error_msg('Could not understand the type: `{}`.'.format(obj.get('type')))
    else:
        return error_msg('Invalid method.')


def poll(request):
    if request.method == 'GET':
        api_key = request.GET.get('api_key', '')
        if len(api_key) != 40:
            return error_msg('Invalid `api_key`.')
        
        try:
            client = Client.get_by_api_key(api_key)
        except:
            return error_msg('Client for `api_key` doesn\'t exist.')
        
        return poll_msg(client.get_managed_configuration())

def fetch(request):
    if request.method == 'GET':
        api_key = request.GET.get('api_key', '')
        file_path = request.GET.get('file_path', '')
        if not file_path:
            return error_msg('Invalid `file_path`.')
        if len(api_key) != 40:
            return error_msg('Invalid `api_key`.')
        
        try:
            client = Client.get_by_api_key(api_key)
        except:
            return error_msg('Client for `api_key` doesn\'t exist.')
        
        try:
            return fetch_msg(client.fetch_configuration(file_path))
        except Exception as e:
            return error_msg('Could not fetch `{}`: {}'.format(file_path, str(e)))


@csrf_exempt
def push(request):
    if request.method == 'POST':
        obj = json.loads(request.body.decode('UTF-8'))
        
        api_key = obj.get('api_key', '')
        if len(api_key) != 40:
            return error_msg('Invalid `api_key`.')
        try:
            client = Client.get_by_api_key(api_key)
        except:
            return error_msg('Client for `api_key` doesn\'t exist.')
        
        file_path = obj.get('file_path', None)
        if file_path is None:
            return error_msg('Invalid `file_path`.')
        if len(file_path) == 0:
            return error_msg('`file_path` cannot be an empty string.')
        mtime = obj.get('mtime', None)
        if mtime is None:
            return error_msg('Invalid `mtime`.')
        if not isinstance(mtime, int):
            return error_msg('`mtime` must be an integer.')
        sha1_checksum = obj.get('sha1_checksum', None)
        if sha1_checksum is None:
            return error_msg('Invalid `sha1_checksum`.')
        content = obj.get('content', None)
        if content is None:
            return error_msg('Invalid `content`.')
        case_sensitive = obj.get('case_sensitive', None)
        if case_sensitive is None:
            return error_msg('Invalid `case_sensitive`.')
        if not isinstance(case_sensitive, bool):
            return error_msg('`case_sensitive` must be boolean.')
        
        try:
            return fetch_msg(client.push_configuration(file_path, case_sensitive, mtime, sha1_checksum, content))
        except Exception as e:
            return error_msg('Could not push `{}`: {}'.format(file_path, str(e)))
