import os, sys
from datetime import date, datetime, timedelta
import time
from hashlib import sha1
import random

from django.db import models


class ClientException(Exception):
    pass

class ConfigurationException(Exception):
    pass


class Client(models.Model):
    client_name = models.CharField(max_length=256, unique=True)
    api_key = models.CharField(max_length=40, unique=True, blank=True)
    date_created = models.DateField(auto_now_add=True)
    is_disabled = models.BooleanField(default=True)
    is_blacklisted = models.BooleanField(default=False)
    
    class Meta:
        managed = True
    
    def __unicode__(self):
        return  '(' + self.api_key[:6] + ') ' + self.client_name
    
    def __str__(self):
        return self.__unicode__()
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.api_key = sha1(str(str(datetime.utcnow().isoformat()) +
                                str(random.uniform(0, 1))).encode('UTF-8')).hexdigest()
        super(Client, self).save(*args, **kwargs)
    
    @staticmethod
    def new_client(name):
        name = name.lower()
        
        try:
            c = Client.objects.get(client_name=name)
            if c.is_blacklisted:
                raise ClientException('Client `{}` is blacklisted.'.format(c.client_name))
            if not c.is_disabled:
                return False
            else:
                c.is_disabled = False
                c.save()
                return c
        except ClientException:
            raise
        except:
            c = Client()
            c.client_name = name
            c.save()
            return c
    
    @staticmethod
    def disable_client(api_key):
        try:
            c = Client.objects.get(api_key=api_key)
            c.is_disabled = True
            c.save()
            return c
        except:
            raise Exception('Invalid `api_key`.')
    
    @staticmethod
    def get_by_api_key(api_key):
        c = Client.objects.get(api_key=api_key)
        return c
    
    @staticmethod
    def get_config_status(api_key):
        try:
            c = Client.objects.get(api_key=api_key)
        except:
            return {'error': 'Could not get client for `api_key`.'}
        
        configs = c.configuration_set.all()
        
        data = {
            'name': c.client_name,
            'is_disabled': c.is_disabled,
            'is_blacklisted': c.is_blacklisted,
            'configurations': [],
        }
        
        if c.is_disabled or c.is_blacklisted:
            return data
        
        for config in configs:
            c_dict = {}
            c_dict['file_path'] = config.file_path
            c_dict['is_disabled'] = config.is_disabled
            if config.is_disabled:
                data['configurations'].append(c_dict)
                continue
            try:
                config_file = config.configurationfile_set.order_by('-revision')[0]
            except IndexError:
                config_file = ConfigurationFile()
            c_dict['revision'] = config_file.revision
            c_dict['sha1_checksum'] = config_file.sha1_checksum
            c_dict['mtime'] = config_file.mtime
            c_dict['content_length'] = len(config_file.content)
            data['configurations'].append(c_dict)
        
        return data
    
    def get_managed_configuration(self):
        details = {
            'client_name': self.client_name,
            'date_created': str(self.date_created),
            'is_disabled': self.is_disabled,
            'is_blacklisted': self.is_blacklisted,
        }
        if self.is_disabled or self.is_blacklisted:
            return details
        
        details['configurations'] = []
        confs = self.configuration_set.all()
        
        file_count = 0
        
        for conf in confs:
            file_count += 1
            configuration = {}
            configuration['file_path'] = conf.file_path
            configuration['is_disabled'] = conf.is_disabled
            if not conf.is_disabled:
                try:
                    conf_file = conf.configurationfile_set.order_by('-revision')[0]
                except IndexError:
                    conf_file = ConfigurationFile()
                configuration['revision'] = conf_file.revision
                configuration['sha1_checksum'] = conf_file.sha1_checksum
                configuration['mtime'] = conf_file.mtime
            details['configurations'].append(configuration)
        
        details['configuration_count'] = file_count
        return details
    
    def fetch_configuration(self, file_path):
        details = {
            'file_path': '',
            'is_disabled': True,
        }
        config = self.configuration_set.filter(file_path=file_path)
        if len(config) == 0:
            return {'error': 'File not found.'}
        if len(config) > 1:
            return {'error': 'Multiple files found.'}
        if len(config) == 1:
            config = config[0]
            details['file_path'] = config.file_path
            details['is_disabled'] = config.is_disabled
            if not config.is_disabled:
                conf_file = config.configurationfile_set.order_by('-revision')[0]
                details['mtime'] = conf_file.mtime
                details['sha1_checksum'] = conf_file.sha1_checksum
                details['content'] = conf_file.content
        return details
    
    def push_configuration(self, file_path, case_sensitive, mtime, sha1_checksum, content):
        if case_sensitive != True:
            file_path = file_path.lower()
        config = self.configuration_set.filter(file_path=file_path)
        if len(config) == 0:
            return {'error': 'File not found.'}
        if len(config) > 1:
            return {'error': 'Multiple files found.'}
        if len(config) == 1:
            config = config[0]
            if config.is_disabled:
                return {'error': 'Configuration file `{}` is disabled.'.format(file_path)}
            calculated_sha1_checksum = sha1(content.encode('UTF-8')).hexdigest()
            if calculated_sha1_checksum != sha1_checksum:
                return {'error': 'Checksum mismatch for file `{}`, aborting.'.format(file_path)}
            
            try:
                try:
                    conf_file = config.configurationfile_set.order_by('-revision')[0]
                except IndexError:
                    conf_file = ConfigurationFile()
                    conf_file.configuration = config
                    conf_file.save()
                if mtime < conf_file.mtime:
                    return {'error': 'Modified timestamp of pushed file is older than configuration, aborting.'}
                if mtime == conf_file.mtime:
                    return {'error': 'Files are the same age, aborting.'}
                conf_file.mtime = int(mtime)
                conf_file.content = content
                conf_file.sha1_checksum = sha1_checksum
                conf_file.save()
                return {'ok': 'Success!'}
            except Exception as e:
                return {'error': str(e)}


class Configuration(models.Model):
    client = models.ForeignKey('Client')
    file_path = models.CharField(max_length=516)
    is_case_sensitive = models.BooleanField(default=True)
    is_disabled = models.BooleanField(default=False)
    
    class Meta:
        managed = True
    
    
    def __unicode__(self):
        return  '(' + self.client.client_name + ') ' + os.path.basename(self.file_path)
    
    
    def __str__(self):
        return self.__unicode__()
    
    
    @staticmethod
    def add(client, file_path, mtime, case_sensitive, payload):
        if not case_sensitive:
            file_path = file_path.lower()
        try:
            conf = Configuration.objects.get(client=client, file_path=file_path)
            raise ConfigurationException('Configuration for `{}` already exists.'.format(file_path))
        except ConfigurationException:
            raise
        except Exception:
            try:
                conf = Configuration(client=client, file_path=file_path, is_case_sensitive=case_sensitive)
                conf.save()
            except:
                raise ConfigurationException('Could not add new configuration for `{}`'.format(file_path))
            try:
                confFile = ConfigurationFile(configuration=conf, sha1_checksum=sha1(payload.encode('UTF-8')).hexdigest(), mtime=mtime, content=payload)
                confFile.save()
            except Exception as e:
                try:
                    conf.delete()
                except:
                    pass
                raise ConfigurationException('Could not add new configuration file for `{}`'.format(file_path))
        return True
    
    
    @staticmethod
    def remove(client, file_path, mtime, case_sensitive, payload):
        if not case_sensitive:
            file_path = file_path.lower()
        try:
            conf = Configuration.objects.get(client=client, file_path=file_path)
        except Exception:
            raise ConfigurationException('Configuration for `{}` doesn\'t exist.'.format(file_path))
        try:
            conf.delete()
            return True
        except:
            raise ConfigurationException('Could not remove configuration file for `{}`'.format(file_path))
            return False


class ConfigurationFile(models.Model):
    configuration = models.ForeignKey('Configuration')
    updated_at = models.DateTimeField(auto_now_add=True)
    revision = models.PositiveIntegerField(default=1)
    sha1_checksum = models.CharField(max_length=40)
    mtime = models.PositiveIntegerField(default=0)
    content = models.TextField()
    
    class Meta:
        ordering = ['-revision']
    
    def __unicode__(self):
        return '{} r{} {}'.format(str(self.configuration), self.revision, self.content[:25])
    
    def __str__(self):
        return self.__unicode__()
    
    def save(self, *args, **kwargs):
        if self.id:
            latest_revision =  ConfigurationFile.objects.filter(configuration=self.configuration).order_by('-revision')[0].revision
            self.id = None
            self.revision = latest_revision + 1
            self.sha1_checksum = sha1(self.content.encode('UTF-8')).hexdigest()
            self.mtime = int(time.time())
        super(ConfigurationFile, self).save(*args, **kwargs)
