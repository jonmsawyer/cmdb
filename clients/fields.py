import uuid

from django.db import models

class MSSQLUUIDField(models.CharField):
    __metaclass__ = models.SubfieldBase
    description = "Universally Unique Identifier (See RFC 4122)"
    
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 36
        super(MSSQLUUIDField, self).__init__(*args, **kwargs)
    
    def db_type(self, connection):
        return 'uniqueidentifier'
    
    def pre_save(self, instance, add):
        try:
            value = getattr(instance, self.attname, None)
        except:
            value = None
        if not value:
            value = str(uuid.uuid4())
            try:
                setattr(instance, self.attname, value)
            except:
                pass
        return value

    def to_python(self, value):
        if not value:
            return
        return value

    def get_db_prep_save(self, value, connection):
        if not value:
            return
        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        if not value:
            return
        return value

class MSSQLXMLField(models.TextField):
    __metaclass__ = models.SubfieldBase
    description = "Text field of type XML"
    
    def __init__(self, *args, **kwargs):
        super(MSSQLXMLField, self).__init__(*args, **kwargs)
    
    def db_type(self, connection):
        return 'xml'
    
    def get_internal_type(self):
        return 'xml'
    
    def to_python(self, value):
        if not value:
            return
        return value

    def get_db_prep_save(self, value, connection):
        if not value:
            return
        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        if not value:
            return
        return value

