import os, sys

def get_input(msg):
    key_in = None
    while key_in == None or key_in == '':
        key_in = input(msg+' ')
    return key_in

def get_config(module):
    try:
        import importlib
        config = importlib.import_module(module)
        config_dict = {}
        #import ..config
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

def check_config(config):
    if not isinstance(config, dict):
        raise ConfigError('`config` parameter must be of type `dict`.')
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
            raise ConfigAttributeError('Missing `{}` attribute in config file. Please run `agent gen_config`.'.format(atr))
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
