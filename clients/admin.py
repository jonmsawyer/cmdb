from django.contrib import admin

from clients.models import Client, Configuration, ConfigurationFile

class ConfigurationInline(admin.TabularInline):
    model = Configuration

class ConfigurationFileInline(admin.StackedInline):
    model = ConfigurationFile

class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'api_key', 'is_disabled', 'is_blacklisted', 'date_created',)
    list_filter = ('client_name', 'is_disabled', 'is_blacklisted',)
    date_hierarchy = 'date_created'
    readonly_fields = ('date_created',)
    search_fields = ['client_name', 'api_key', 'date_created',]
    inlines = [ConfigurationInline,]
admin.site.register(Client, ClientAdmin)

class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('file_path', 'client', 'is_case_sensitive', 'is_disabled',)
    list_filter = ('client__client_name', 'is_case_sensitive', 'is_disabled',)
    #date_hierarchy = 'log_time'
    #readonly_fields = ('log_time',)
    search_fields = ['client', 'file_path',]
    inlines = [ConfigurationFileInline,]
admin.site.register(Configuration, ConfigurationAdmin)

class ConfigurationFileAdmin(admin.ModelAdmin):
    #list_display = ('short_django_sessionid', 'log_time', 'ip', 'url', 'referrer', 'method')
    #list_filter = ('log_time', 'method')
    #date_hierarchy = 'log_time'
    #readonly_fields = ('log_time',)
    #search_fields = ['django_sessionid', 'ip', 'user_agent', 'log_time', 'juror_id', 'annual_nbr']
    pass
admin.site.register(ConfigurationFile, ConfigurationFileAdmin)
