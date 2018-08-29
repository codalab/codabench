from storages.backends.azure_storage import AzureStorage


class CodalabAzureStorage(AzureStorage):

    def __init__(self, *args, **kwargs):
        if 'azure_container' in kwargs:
            self.azure_container = kwargs.pop('azure_container')
        super().__init__(*args, **kwargs)
