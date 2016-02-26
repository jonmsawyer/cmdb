import os, sys
import requests
import socket
import json
from datetime import date, time, datetime, timedelta
import subprocess

log_file_path = None
agent_config = None

def init_log_file(config):
    global log_file_path
    
    if log_file_path is None:
        if hasattr(config, 'POLL_LOG_FILE') and hasattr(config, 'AGENT_ROOT_DIR'):
            log_file_path = os.path.join(getattr(config, 'AGENT_ROOT_DIR'), getattr(config, 'POLL_LOG_FILE'))


def log(msg, level='INFO', stdout=True):
    global agent_config
    global log_file_path
    name = 'POLL'
    now = datetime.now().isoformat(' ')
    
    if log_file_path is None and agent_config is not None:
        init_log_file(agent_config)
    else:
        log_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'poll.log')
    
    with open(log_file_path, 'a') as fh:
        log_msg = '{name} | {now} | {level} | {msg}\n'.format(
            name=name, now=now, level=level, msg=msg)
        fh.write(log_msg)
        if stdout == True:
            print(log_msg)


def get_input(msg):
    if not msg.endswith(' '):
        msg += ' '
    key_in = None
    while key_in is None:
        key_in = input(msg)
    return key_in


def install_scheduled_task(args, config):
    global agent_config
    agent_config = config
    
    agent_root_dir = None
    if hasattr(config, 'AGENT_ROOT_DIR'):
        agent_root_dir = getattr(config, 'AGENT_ROOT_DIR')
        if not os.path.isdir(agent_root_dir):
            log('Could not get AGENT_ROOT_DIR config, `{}` is not a valid directory on this system.')
            agent_root_dir = None
    if not agent_root_dir:
        log('Unable to install the scheduled task -- please ensure that AGENT_ROOT_DIR is set properly in config.py')
        sys.exit(1)
    script_path = os.path.join(agent_root_dir, 'lib', 'install_schtask.bat')
    agent_py = os.path.join(agent_root_dir, 'agent.py')
    python_exec = sys.executable
    
    # prefer pythonw.exe on windows
    python_dir = os.path.dirname(python_exec)
    if os.path.isfile(os.path.join(python_dir, 'pythonw.exe')):
        python_exec = os.path.join(python_dir, 'pythonw.exe')
    # /prefer
    
    if os.path.isfile(script_path):
        log('Installing scheduled task...')
        ret_code = subprocess.call([script_path, python_exec, agent_py])
        log('... Return code from script: {}'.format(ret_code))
        log('... Done!')
        sys.exit(ret_code)


def remove_scheduled_task(args, config):
    global agent_config
    agent_config = config
    
    agent_root_dir = None
    if hasattr(config, 'AGENT_ROOT_DIR'):
        agent_root_dir = getattr(config, 'AGENT_ROOT_DIR')
        if not os.path.isdir(agent_root_dir):
            log('Could not get AGENT_ROOT_DIR config, `{}` is not a valid directory on this system.'.format(agent_root_dir))
            agent_root_dir = None
    if not agent_root_dir:
        log('Unable to install the scheduled task -- please ensure that AGENT_ROOT_DIR is set properly in config.py')
        sys.exit(1)
    script_path = os.path.join(agent_root_dir, 'lib', 'remove_schtask.bat')
    if os.path.isfile(script_path):
        log('Removing scheduled task...')
        ret_code = subprocess.call([script_path])
        log('... Return code from script: {}'.format(ret_code))
        log('... Done!')
        sys.exit(ret_code)
