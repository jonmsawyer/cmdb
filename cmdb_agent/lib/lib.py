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


class ConfigFileError(Exception):
    pass

class LocalConfigFileError(ConfigFileError):
    pass

class RemoteConfigFileError(ConfigFileError):
    pass

class ConfigFileComparisonError(ConfigFileError):
    pass

class BaseConfigFile(object):
    config = {
        'file_path': None,
        'is_binary': None,
        'is_encrypted': False,
        'is_case_sensitive': None,
        'is_disabled': None,
        'mtime': -1,
        'sha1_checksum': None,
        'content': None,
        'content_length': None,
    }
    is_resolved = False
    path = None
    stat = None
    encryption_key = None
    is_encryptable = False
    binary_mode = False
    config_file_type = None
    config_dict = None # the config.py config dict as given by lib.get_config()
    
    def __init__(self, file_path, config_dict=None, encryption_key=None, binary_mode=False, *args, **kwargs):
        self.config['file_path'] = file_path
        self.path = Path(file_path)
        if isinstance(config_dict, dict):
            self.config_dict = check_config(config_dict)
        try:
            self.stat = self.path.resolve().stat()
        except:
            self.stat = None
        self.is_resolved = False
        self.binary_mode = bool(binary_mode)
        if encryption_key is not None:
            key_len = 32
            if not isinstance(encryption_key, str):
                raise LocalConfigFileError('Encryption key must be a url-safe 32 character ascii string.')
            if len(encryption_key[:key_len]) != key_len:
                raise LocalConfigFileError('Encryption key must be a url-safe 32 character ascii string.')
            self.encryption_key = base64.b64encode(encryption_key.encode('ascii'))
            Fernet(self.encryption_key) # try it out, if no exception, we're good
            self.is_encryptable = True
    
    def __lt__(self, other):
        if self.config.get('mtime') == -1 or \
           other.config.get('mtime') == -1:
                raise ConfigFileComparisonError('mtime error: mtime must be set.')
        return self.config.get('mtime') < other.config.get('mtime')
    
    def __le__(self, other):
        if self.config.get('mtime') == -1 or \
           other.config.get('mtime') == -1:
                raise ConfigFileComparisonError('mtime error: mtime must be set.')
        return self.config.get('mtime') <= other.config.get('mtime')
    
    def __eq__(self, other):
        if self.config.get('sha1_checksum') is None or \
           other.config.get('sha1_checksum') is None:
                raise ConfigFileComparisonError('checksum error: checksums must be set.')
        if self.config.get('mtime') == -1 or \
           other.config.get('mtime') == -1:
                raise ConfigFileComparisonError('mtime error: mtime must be set.')
        
        if self.config.get('sha1_checksum') == other.config.get('sha1_checksum'):
            return self.config.get('mtime') == other.config.get('mtime')
        else:
            return False
    
    def __ne__(self, other):
        return not self == other
    
    def __gt__(self, other):
        return not self <= other
    
    def __ge__(self, other):
        return not self < other
    
    def is_binary(self):
        if self.config.get('is_binary') is not None:
            return self.config.get('is_binary')
        else:
            return None
    
    def encrypt(self, save_content=False):
        if self.encryption_key is None:
            raise Exception('Cannot encrypt content, missing encryption key.')
        if self.config.get('content') is None:
            raise Exception('Cannot encrypt content, content is empty.')
        if self.is_encryptable == False:
            raise Exception('Cannot encrypt, improper configuration.')
        if self.config.get('is_encrypted') == True:
            return self.config.get('content')
        
        f = Fernet(self.encryption_key)
        if self.config.get('is_binary') == True:
            encr_content = f.encrypt(self.config.get('content'))
        elif self.config.get('is_binary') == False:
            encr_content = f.encrypt(self.config.get('content').encode('utf-8')).decode('utf-8')
        else:
            raise Exception('Could not tell if file is binary or text. Aborting.')
        if save_content == True:
            try:
                self.config['content'] = encr_content
                self.config['content_length'] = len(encr_content)
                self.config['is_encrypted'] = True
            except:
                raise
        return encr_content
    
    def decrypt(self, save_content=False):
        if self.encryption_key is None:
            raise LocalConfigFileError('Cannot decrypt content, missing encryption key.')
        if self.config.get('content') is None:
            raise LocalConfigFileError('Cannot decrypt content, content is empty.')
        if self.is_encryptable == False:
            raise LocalConfigFileError('Cannot decrypt, improper configuration.')
        if self.config.get('is_encrypted') == False:
            return self.config.get('content')
        
        f = Fernet(self.encryption_key)
        if self.config.get('is_binary') == True:
            decr_content = f.decrypt(self.config.get('content'))
        elif self.config.get('is_binary') == False:
            decr_content = f.decrypt(self.config.get('content').encode('utf-8')).decode('utf-8')
        else:
            raise LocalConfigFileError('Could not tell if file is binary or text. Aborting.')
        if save_content == True:
            try:
                self.config['content'] = decr_content
                self.config['content_length'] = len(decr_content)
                self.config['is_encrypted'] = False
            except:
                raise
        return decr_content
    
    def get_config(self):
        return dict(self.config)
    
    def get_config_json(self):
        return json.dumps(self.config)
    
    def checksum(self):
        if self.config.get('sha1_checksum') is not None:
            return self.config.get('sha1_checksum')
        else:
            if self.config.get('content') is not None:
                if self.config.get('is_binary') == False:
                    return sha1(self.config.get('content').encode('utf-8')).hexdigest()
                else:
                    return sha1(self.config.get('content')).hexdigest()
            else:
                return None
    
    def resolve(self):
        try:
            self.config['file_path'] = str(self.path)
            self.read(self.binary_mode)
            self.is_resolved = True
            return self.is_resolved                
        except:
            raise
    
    def read(self, binary=False):
        raise Exception('Method `read` must be overridden in derived class.')
    
    def is_case_sensitive(self):
        raise Exception('Method `is_case_sensitive` must be overridden in derived class.')


class LocalConfigFile(BaseConfigFile):
    def __init__(self, file_path, config_dict=None, *args, **kwargs):
        self.config_file_type = 'local'
        super(LocalConfigFile, self).__init__(file_path, config_dict, *args, **kwargs)
    
    def read(self, binary=False):
        with open(str(self.path), 'rb') as fh:
            buf = fh.read()
        try:
            if binary == True:
                raise Exception('Forcing binary mode.')
            buf = buf.decode('UTF-8')
            # buf had no problems decoding, let's flag this as non-binary and
            # re-read the file in text mode to take care of line endings
            # automagically.
            with open(str(self.path), 'r') as fh:
                buf = fh.read()
            self.config['is_binary'] = False
        except:
            self.config['is_binary'] = True
        self.config['is_encrypted'] = False
        self.config['is_case_sensitive'] = self.is_case_sensitive()
        self.config['is_disabled'] = False
        self.config['mtime'] = int(self.stat.st_mtime)
        self.config['sha1_checksum'] = self.checksum()
        self.config['content'] = buf
        self.config['content_length'] = len(buf)
        return buf
    
    def is_case_sensitive(self):
        cs = True
        temp_handle, temp_path = tempfile.mkstemp()
        if os.path.exists(temp_path.upper()):
            cs = False
        os.close(temp_handle)
        os.unlink(temp_path)
        return cs    
    
    def resolve(self):
        try:
            self.path = self.path.resolve()
            self.stat = self.path.stat()
            self.config['file_path'] = str(self.path)
            self.read(self.binary_mode)
            self.is_resolved = True
            return self.is_resolved
        except:
            raise

class RemoteConfigFile(BaseConfigFile):
    def __init__(self, file_path, config_dict, encryption_key=None, binary_mode=False, *args, **kwargs):
        self.config_file_type = 'remote'
        super(RemoteConfigFile, self).__init__(file_path, config_dict, encryption_key=encryption_key, binary_mode=binary_mode, *args, **kwargs)
    
    def read(self, binary_mode=False):
        path = '/clients/fetch/'
        url = get_config_url(self.config_dict, path)
        api_key = get_config_api_key(self.config_dict)
        req = requests.get(url, params={'api_key': api_key, 'file_path': self.config.get('file_path')})
        payload = get_response_body(req)
        payload = json.loads(payload)
        
        self.config['is_binary'] = payload.get('is_binary')
        self.config['is_encrypted'] = payload.get('is_encrypted')
        self.config['is_case_sensitive'] = payload.get('is_case_sensitive')
        self.config['is_disabled'] = payload.get('is_disabled')
        self.config['mtime'] = payload.get('mtime', -1)
        self.config['sha1_checksum'] = payload.get('sha1_checksum')
        self.config['content'] = payload.get('content')
        self.config['content_length'] = payload.get('content_length')
        
        return payload.get('content')
    
    def is_case_sensitive(self):
        return self.config.get('is_case_sensitive')

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
        ('POLL_LOG_FILE', str)
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
        sys.exit(1)
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
        sys.exit(1)

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
