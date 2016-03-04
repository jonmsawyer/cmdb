# System
import os, tempfile
from pathlib import Path
from hashlib import sha1
import base64
import json

# 3rd Party
from cryptography.fernet import Fernet
import requests

# Local
import lib.lib as lib

# Local exceptions
class ConfigError(Exception): pass
class AgentConfigError(ConfigError): pass
class AgentConfigAttributeError(AgentConfigError): pass
class LocalConfigError(ConfigError): pass
class LocalConfigAttributeError(LocalConfigError): pass
class RemoteConfigError(ConfigError): pass
class RemoteConfigAttributeError(RemoteConfigError): pass


class Config(object):
    meta_config = {
        'file_path': None,
        'is_binary': None,
        'is_encrypted': False,
        'is_case_sensitive': None,
        'is_disabled': None,
        'sha1_checksum': None,
        'mtime': -1,
        'content': None,
        'content_length': None,
        'ciphertext': None,
        'ciphertext_length': None,
    }
    
    def __init__(self, file_path, agent_config, *args, **kwargs):
        self.local_config = dict(self.meta_config)
        self.local_path = None
        self.is_local_resolved = False
        
        self.remote_config = dict(self.meta_config)
        self.remote_path = None
        self.is_remote_resolved = False
        
        self.file_path = file_path
        self.agent_config = agent_config
        self._check_agent_config()
    
    def _check_agent_config(self):
        if not isinstance(self.agent_config, dict):
            raise ConfigError('`config_dict` parameter must be of type `dict`.')
        config = self.agent_config
        valid_attrs = (
            ('AGENT_ROOT_DIR', str),
            ('HOSTNAME', str),
            ('PORT', int),
            ('URI', str),
            ('API_KEY', str),
            ('ENCRYPTION_KEY', str),
        )
        for atr, t in valid_attrs:
            if not atr in config:
                raise AgentConfigAttributeError('Missing `{}` attribute in config file. Please run `agent genconfig`.'.format(atr))
            if not isinstance(config.get(atr), t):
                raise AgentConfigError('Attribute `{}` must be of `{}`, instead it is of `{}`.'.format(
                    atr, str(t), config.get(atr).__class__)
                )
    
    def _get_local_content(self, file_path):
        if self.local_config.get('content') is not None:
            return self.local_config.get('content')
        with open(file_path, 'rb') as fh:
            buf = fh.read()
        try:
            buf.decode('UTF-8')
            with open(file_path, 'r') as fh:
                buf = fh.read()
        except:
            pass
        return buf
    
    def _get_remote_content(self, file_path=None):
        return self.remote_config.get('content')
    
    def _is_local_case_sensitive(self):
        if self.local_config.get('is_case_sensitive') is not None:
            return self.local_config.get('is_case_sensitive')
        cs = True
        temp_handle, temp_path = tempfile.mkstemp()
        if os.path.exists(temp_path.upper()):
            cs = False
        os.close(temp_handle)
        os.unlink(temp_path)
        return cs
    
    def _is_remote_case_sensitive(self):
        return self.remote_config.get('is_case_sensitive')
    
    def _checksum(self, buf):
        if type(buf) == str:
            buf = buf.encode('UTF-8')
        elif type(buf) == bytes:
            pass
        else:
            raise ConfigError('Paramater `buf` must be a `bytes` or `str` object. Instead, it is `{}`'.format(str(type(buf))))
        
        checksum = sha1(buf).hexdigest()
        return checksum
    
    def resolve_local(self):
        if self.is_local_resolved == True:
            return self.is_local_resolved
        try:
            self.local_path = Path(self.file_path)
            self.local_path = self.local_path.resolve()
            self.local_config['file_path'] = self.file_path
            self.local_config['mtime'] = int(self.local_path.stat().st_mtime)
            self.local_config['content'] = self._get_local_content(self.file_path)
            if type(self.local_config['content']) == bytes:
                self.local_config['is_binary'] = True
            elif type(self.local_config['content']) == str:
                self.local_config['is_binary'] = False
            else:
                pass
            self.local_config['is_case_sensitive'] = self._is_local_case_sensitive()
            self.local_config['content_length'] = len(self.local_config['content'])
            self.local_config['sha1_checksum'] = self._checksum(self.local_config['content'])
            self.is_local_resolved = True
            return self.is_local_resolved
        except:
            raise
    
    def resolve_remote(self):
        if self.is_remote_resolved == True:
            return self.is_remote_resolved
        path = '/clients/fetch/'
        url = lib.get_config_url(self.agent_config, path)
        api_key = lib.get_config_api_key(self.agent_config)
        req = requests.get(url, params={'api_key': api_key, 'file_path': self.file_path})
        payload = lib.get_response_body(req)
        payload = json.loads(payload)
        
        if payload.get('error') is not None:
            raise FileNotFoundError('Could not retrieve remote file `{}`: {}'.format(self.file_path, payload.get('error')))
        
        try:
            self.remote_config['file_path'] = self.file_path
            self.remote_config['is_binary'] = payload.get('is_binary')
            self.remote_config['is_encrypted'] = payload.get('is_encrypted')
            self.remote_config['is_case_sensitive'] = payload.get('is_case_sensitive')
            self.remote_config['is_disabled'] = payload.get('is_disabled')
            self.remote_config['mtime'] = payload.get('mtime')
            self.remote_config['sha1_checksum'] = payload.get('sha1_checksum')
            self.remote_config['content'] = payload.get('content')
            self.remote_config['content_length'] = payload.get('content_length')
            self.is_remote_resolved = True
            return self.is_remote_resolved
        except:
            raise
    
    def resolve(self):
        local_ret = None
        remote_ret = None
        try:
            local_ret = self.resolve_local()
        except Exception as e:
            local_ret = str(e)
        try:
            remote_ret = self.resolve_remote()
        except Exception as e:
            remote_ret = str(e)
        return (local_ret, remote_ret)
    
    def compare(self, mode='both'):
        """
        Return:
         * Return -1 if the local file is newer than the remote file
           * Result: local file is pushed to the server
         * Return  0 if the local file is the same age as the remote file
           and if their checksums match
           * Result: no file is synced
         * Return  1 if the local file is older than the remote file
           * Result: remote file is retrieved from the server
         * Return False if the local file remote file are the same age, but
           their checksums do not match
         * Return None if no logical comparison could be made
        
        Visual:
           [ -1: local file is newer | 0: same age | 1: remote file is newer ]
        """
        try:
            mode = mode.lower()
        except:
            raise ConfigError('Parameter `mode` must be a string.')
        if mode not in ('both', 'mtime', 'checksum'):
            raise ConfigError("Parameter `mode` must be one of 'both', 'mtime', or 'checksum'.")
        if self.is_local_resolved != True:
            raise ConfigError('Local file needs to be resolved before comparing with remote file.')
        if self.is_remote_resolved != True:
            raise ConfigError('Remote file needs to be resolved before comparing with local file.')
        
        local_mtime = self.local_config.get('mtime')
        local_checksum = self.local_config.get('sha1_checksum')
        remote_mtime = self.remote_config.get('mtime')
        remote_checksum = self.remote_config.get('sha1_checksum')
        
        if mode == 'both':
            if local_mtime > remote_mtime:
                return -1
            if local_mtime < remote_mtime:
                return 1
            if local_mtime == remote_mtime:
                if local_checksum == remote_checksum:
                    return 0
                else:
                    return False
            return None
        elif mode == 'mtime':
            if local_mtime > remote_mtime:
                return -1
            if local_mtime < remote_mtime:
                return 1
            if local_mtime == remote_mtime:
                return 0
            return None
        elif mode == 'checksum':
            return local_checksum == remote_checksum
        else:
            return None
    
    def push_local(self):
        if self.is_local_resolved != True:
            raise ConfigError('Local file needs to be resolved before pushing to remote server.')
        
        url = lib.get_config_url(self.agent_config, '/clients/push/')
        
        data = self.local_config.copy()
        data['api_key'] = lib.get_config_api_key(self.agent_config)
        
        req = requests.post(url, data=json.dumps(data))
        resp_body = lib.get_response_body(req)
        payload = json.loads(resp_body)
        lib.check_for_error(payload)
        self.is_remote_resolved = False
        return payload
    
    def fetch_remote(self):
        pass
    
    def sync(self):
        pass




class ConfigFileError(Exception):
    pass

class LocalConfigFileError(ConfigFileError):
    pass

class RemoteConfigFileError(ConfigFileError):
    pass

class ConfigFileComparisonError(ConfigFileError):
    pass

class BaseConfigFile(object):
    def __init__(self, file_path, config_dict=None, encryption_key=None, binary_mode=False, *args, **kwargs):
        self.config = {
            'file_path': file_path,
            'is_binary': None,
            'is_encrypted': False,
            'is_case_sensitive': None,
            'is_disabled': None,
            'mtime': -1,
            'sha1_checksum': None,
            'content': None,
            'content_length': None,
        }
        self.is_resolved = False
        self.is_file_not_found = None
        self.path = Path(file_path)
        self.stat = None
        self.encryption_key = None
        self.is_encryptable = False
        self.binary_mode = False
        self.config_file_type = None
        self.config_dict = None

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
        if self.config.get('mtime') == -1:
            raise ConfigFileComparisonError('mtime error: lhs mtime must be set.')
        if other.config.get('mtime') == -1:
            raise ConfigFileComparisonError('mtime error: rhs mtime must be set.')
        return self.config.get('mtime') < other.config.get('mtime')
    
    def __le__(self, other):
        if self.config.get('mtime') == -1:
            raise ConfigFileComparisonError('mtime error: lhs mtime must be set.')
        if other.config.get('mtime') == -1:
            raise ConfigFileComparisonError('mtime error: rhs mtime must be set.')
        return self.config.get('mtime') <= other.config.get('mtime')
    
    def __eq__(self, other):
        if self.config.get('sha1_checksum') is None:
            raise ConfigFileComparisonError('checksum error: lhs checksum must be set.')
        if other.config.get('sha1_checksum') is None:
            raise ConfigFileComparisonError('checksum error: rhs checksum must be set.')
        if self.config.get('mtime') == -1:
            raise ConfigFileComparisonError('mtime error: lhs mtime must be set.')
        if other.config.get('mtime') == -1:
            raise ConfigFileComparisonError('mtime error: rhs mtime must be set.')
        
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
        raise Exception('Method `resolve` must be overridden in derived class.')
    
    def read(self, binary=False):
        raise Exception('Method `read` must be overridden in derived class.')
    
    def is_case_sensitive(self):
        raise Exception('Method `is_case_sensitive` must be overridden in derived class.')


class LocalConfigFile(BaseConfigFile):
    def __init__(self, file_path, config_dict=None, *args, **kwargs):
        self.config_file_type = 'local'
        super(LocalConfigFile, self).__init__(file_path, config_dict, *args, **kwargs)
    
    def read(self, binary=False):
        if self.is_file_not_found == True:
            return None
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
            try:
                self.path = self.path.resolve()
                self.stat = self.path.stat()
                self.is_file_not_found = False
            except:
                self.is_file_not_found = True
            self.read(self.binary_mode)
            self.is_resolved = True
            return self.is_resolved
        except:
            raise
    
    def save_remote(self, config_dict=None):
        if config_dict is not None:
            self.config_dict = check_config(config_dict)
        path = '/clients/push/'
        url = get_config_url(self.config_dict, path)
        api_key = get_config_api_key(self.config_dict)
        if self.is_encoded == False:
            self.config['content'] = base64.b64encode(self.config.get('content'))
            self.is_encoded = True
        req = requests.post(url, params={'api_key': api_key, 'file_path': self.config.get('file_path')})
        payload = get_response_body(req)
        payload = json.loads(payload)


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
        
        if payload.get('error') is not None:
            self.is_file_not_found = True
            return None
        
        self.config['is_binary'] = payload.get('is_binary')
        self.config['is_encrypted'] = payload.get('is_encrypted')
        self.config['is_case_sensitive'] = payload.get('is_case_sensitive')
        self.config['is_disabled'] = payload.get('is_disabled')
        self.config['mtime'] = payload.get('mtime', -1)
        self.config['sha1_checksum'] = payload.get('sha1_checksum')
        self.config['content'] = payload.get('content')
        self.config['content_length'] = payload.get('content_length')
        self.is_file_not_found = False

        return payload.get('content')
    
    def resolve(self):
        try:
            self.config['file_path'] = str(self.path)
            self.read(self.binary_mode)
            self.is_resolved = True
            return self.is_resolved                
        except:
            raise
    
    def is_case_sensitive(self):
        return self.config.get('is_case_sensitive')
