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
            raise ConfigError('Missing `{}` attribute in config file.'.format(atr))
        if not isinstance(getattr(config, atr), t):
            raise ConfigError('Attribute `{}` must be of `{}`, instead it is of `{}`.'.format(atr, str(t), getattr(config, atr).__class__))
    return config
