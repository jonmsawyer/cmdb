# System
import os, sys, tempfile
from pathlib import Path
from hashlib import sha1
from datetime import datetime
import base64
import json

# 3rd Party
from cryptography.fernet import Fernet
import requests


def get_input(msg, default=''):
    key_in = None
    while key_in == None or key_in == '':
        if default:
            key_in = input(msg+' [{}] '.format(default))
            if key_in == '':
                return default
        else:
            key_in = input(msg+' ')
    return key_in

def get_config(module):
    try:
        import importlib
        config = importlib.import_module(module)
        config_dict = {}
        for attribute in dir(config):
            if attribute.startswith('__'):
                continue
            config_dict[attribute] = getattr(config, attribute)
        return config_dict
    except:
        return {}

class ConfigError(Exception):
    pass

class ConfigAttributeError(ConfigError):
    pass

def check_config(config, args=None):
    if not isinstance(config, dict):
        raise ConfigError('`config` parameter must be of type `dict`.')
    if args and 'genconfig' in args:
        return config
    valid_attrs = (
        ('AGENT_ROOT_DIR', str),
        ('HOSTNAME', str),
        ('PORT', int),
        ('URI', str),
        ('API_KEY', str),
        ('POLL_LOG_FILE', str),
        ('ENCRYPTION_KEY', str),
    )
    for atr, t in valid_attrs:
        if not atr in config:
            raise ConfigAttributeError('Missing `{}` attribute in config file. Please run `agent genconfig`.'.format(atr))
        if not isinstance(config.get(atr), t):
            raise ConfigError('Attribute `{}` must be of `{}`, instead it is of `{}`.'.format(
                atr, str(t), config.get(atr).__class__)
            )
    return config

def get_config_api_key(config):
    config = check_config(config)
    return config.get('API_KEY')

def get_config_url(config, path=''):
    config = check_config(config)
    hostname = config.get('HOSTNAME')
    port = config.get('PORT')
    uri = config.get('URI')
    if not uri.startswith('/'):
        uri = '/{}'.format(uri)
    if not isinstance(path, str):
        raise ConfigError('`path` parameter must be of type `<class \'str\'>`')
    if path:
        if uri.endswith('/'):
            uri = uri[:-1]
        if not path.startswith('/'):
            path = '/{}'.format(path)
        if not path.endswith('/'):
            path = '{}/'.format(path)
    return "http://{hostname}:{port}{uri}{path}".format(
        hostname=config.get('HOSTNAME'),
        port=config.get('PORT'),
        uri=config.get('URI'),
        path=path)

def get_config_uri(config):
    config = check_config(config)
    hostname = config.get('HOSTNAME')
    port = config.get('PORT')
    uri = config.get('URI')
    if not uri.startswith('/'):
        uri = '/{}'.format(uri)
    return "http://{hostname}:{port}{uri}".format(
        hostname=config.get('HOSTNAME'),
        port=config.get('PORT'),
        uri=config.get('URI'))

def get_response_body(request):
    err_file = r'c:\cmdb_error.html'
    resp_body = request.content.decode('UTF-8')
    if request.status_code != 200:
        with open(err_file, 'w') as fh:
            fh.write(resp_body)
        print('There was an error, check `{}`.'.format(err_file))
        return {'error': 'There was an error, check `{}`.'.format(err_file)}
        #sys.exit(1)
    return resp_body

class RequireKeyError(Exception):
    pass

def require_key(dictionary, key, _type=None):
    if not isinstance(dictionary, dict):
        raise RequireKeyError('`dictionary` parameter must be of type `<class \'dict\'>`.')
    if not isinstance(key, str):
        raise RequireKeyError('`key` parameter must be of type `<class \'str\'>`.')
    if _type is not None:
        if not isinstance(dictionary.get(key), _type):
            raise RequireKeyError('The value type of `{}` must be of type `{}`.'.format(dictionary.get(key), str(_type)))
    if key not in dictionary:
        raise RequireKeyError('Could not find `{}` key in object.'.format(key))
    return dictionary.get(key)

def check_for_error(dictionary):
    if not isinstance(dictionary, dict):
        raise Exception('`dictionary` parameter must be of type `{}`.'.format(str(dict)))
    if 'error' in dictionary:
        print(dictionary.get('error'))
        return
        #sys.exit(1)

def is_case_sensitive():
    cs = True
    temp_handle, temp_path = tempfile.mkstemp()
    if os.path.exists(temp_path.upper()):
        cs = False
    os.close(temp_handle)
    os.unlink(temp_path)
    return cs

def check_local_file(config):
    '''
    input:
    
    config: {
      "file_path": str,
      "mtime": int,
      "sha1_checksum": str,
      "is_disabled": bool,
      "revision": int,
      "is_binary": bool,
      "is_encrypted": bool
    }
    
    output:
    
    12345      file r#
    
    Where 1 is one of '>', '<', '=', '?', 'E':
      * > local file is newer than server, next sync will update the file on server
      * < local file is older than server, next sync will update the file on filesystem
      * = local file and server file are the same, next sync will ignore this file
      * ? local file is missing, next sync will update the file on the filesystem
      * E error calculating status field 1
    
    Where 2 is one of ' ', 'C', 'E':
      *   local file and remote file's checksums match
      * C local file and remote file's checksums do not match
      * E error calculating status field 2
    
    Where 3 is one of ' ', 'D', 'E':
      *   no status to display
      * D remote file is disabled, next sync will ignore this file
      * E error calculating status field 3
  
    Where 4 is one of ' ', 'B', 'E':
     *   remote file is a text file
     * B remote file is a binary file
     * E error determining if remote file is text or binary
    
    Where 5 is one of ' ', '#', 'E':
     *   remote file is not encrypted
     * # remote file is encrypted
    
    Where file is the remote file name
    
    Where # is the revision of the remote file
    '''
    line = ''
    
    try:
        file_path = str(Path(config.get('file_path')).resolve())
        file_exists = True
    except:
        file_path = config.get('file_path')
        file_exists = False
    
    try:
        st = os.stat(file_path)
        mtime = int(st.st_mtime)
    except:
        mtime = 0
    
    try:
        with open(file_path, 'r') as fh:
            buf = fh.read()
        sha1_checksum = sha1(buf.encode('UTF-8')).hexdigest()
        if sha1_checksum == config.get('sha1_checksum'):
            checksums_match = True
        else:
            checksums_match = False
    except:
        sha1_checksum = buf = ''
        checksums_match = False
    
    is_disabled = config.get('is_disabled')
    
    # Calculate column 1
    if file_exists == False:
        line += '?'
    else:
        if mtime > config.get('mtime', -1):
            line += '>'
        elif mtime < config.get('mtime', -1):
            line += '<'
        elif mtime == config.get('mtime', -1):
            line += '='
        else:
            line += 'E'
    
    # Calculate column 2
    if checksums_match == True:
        line += ' '
    elif checksums_match == False:
        line += 'C'
    else:
        line += 'E'
    
    # Calculate column 3
    if config.get('is_disabled') == True:
        line += 'D'
    elif config.get('is_disabled') == False:
        line += ' '
    else:
        line += 'E'
    
    # Calculate column 4
    if config.get('is_binary') == True:
        line += 'B'
    elif config.get('is_binary') == False:
        line += ' '
    else:
        line += 'E'
    
    # Calculate column 5
    if config.get('is_encrypted') == True:
        line += '#'
    elif config.get('is_encrypted') == False:
        line += ' '
    else:
        line += 'E'
    
    line += '      {} r{}'.format(file_path, config.get('revision', -1))
    return line

def get_config_log_file_path(config):
    return os.path.join(config.get('AGENT_ROOT_DIR'), config.get('POLL_LOG_FILE'))

def log(msg, level='INFO', stdout=True, name='SYNC'):
    log_file_path = get_config_log_file_path(get_config('config'))
    now = datetime.now().isoformat(' ')
    
    with open(log_file_path, 'a') as fh:
        log_msg = '{name} | {now} | {level} | {msg}\r\n'.format(
            name=name, now=now, level=level, msg=msg)
        fh.write(log_msg)
        if stdout == True:
            print(msg)
