import hashlib
import json
import logging

from django.conf import settings
from django.db import models

from chahub.tasks import send_to_chahub, delete_from_chahub

logger = logging.getLogger(__name__)


class ChaHubModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)

    def all_objects(self):
        return super().get_queryset()


class ChaHubSaveMixin(models.Model):
    """Helper mixin for saving model data to ChaHub.

    To use:
    1) Override `get_chahub_endpoint()` to return the endpoint on ChaHub API for this model
    2) Override `get_chahub_data()` to return a dictionary to send to ChaHub
    3) Override `get_whitelist()` to return a whitelist of fields to send to ChaHub if obj not public
    4) Be sure to call `self.clean_private_data()` inside `get_chahub_data`
    5) Override `get_chahub_is_valid()` to return True/False on whether or not the object is ready to send to ChaHub
    6) Data is sent on `save()` and `chahub_timestamp` timestamp is set

    To update remove the `chahub_timestamp` timestamp and call `save()`"""
    # Timestamp set whenever a successful update happens
    chahub_timestamp = models.DateTimeField(null=True, blank=True)

    # A hash of the last json information that was sent to avoid sending duplicate information
    chahub_data_hash = models.TextField(null=True, blank=True)

    # If sending to chahub fails, we may need a retry. Signal that by setting this attribute to True
    chahub_needs_retry = models.BooleanField(default=False)

    # Set to true if celery attempt at deletion does not get a 204 resp from chahub, so we can retry later
    deleted = models.BooleanField(default=False)

    objects = ChaHubModelManager()

    class Meta:
        abstract = True

    @property
    def app_label(self):
        return f'{self.__class__._meta.app_label}.{self.__class__.__name__}'

    def get_whitelist(self):
        """Override this to set the return the whitelisted fields for private data
        Example:
            return ['remote_id', 'is_public']
        """
        raise NotImplementedError()

    # -------------------------------------------------------------------------
    # METHODS TO OVERRIDE WHEN USING THIS MIXIN!
    # -------------------------------------------------------------------------
    @staticmethod
    def get_chahub_endpoint():
        """Override this to return the endpoint URL for this resource

        Example:
            # If the endpoint is chahub.org/api/v1/competitions/ then...
            return "competitions/"
        """
        raise NotImplementedError()

    def get_chahub_data(self):
        """Override this to return a dictionary with data to send to chahub

        Example:
            return {"name": self.name}
        """
        raise NotImplementedError()

    def get_chahub_is_valid(self):
        """Override this to validate the specific model before it's sent

        Example:
            return comp.is_published
        """
        # By default, always push
        return True

    def clean_private_data(self, data):
        """Override this to clean up any data that should not be sent to chahub if the object is not public"""
        if hasattr(self, 'is_public'):
            public = self.is_public
        elif hasattr(self, 'published'):
            public = self.published
        else:
            # assume data is good to push to chahub if there is no field saying otherwise
            public = True
        if not public:
            for key in data.keys():
                if key not in self.get_whitelist():
                    data[key] = None
        return data

    # Regular methods
    def save(self, send=True, *args, **kwargs):
        # We do a save here to give us an ID for generating URLs and such
        super().save(*args, **kwargs)

        # making sure get whitelist was implemented, making sure we don't send to chahub without cleaning our data
        self.get_whitelist()

        if getattr(settings, 'IS_TESTING', False) and not getattr(settings, 'PYTEST_FORCE_CHAHUB', False):
            # For tests let's just assume Chahub isn't available
            # We can mock proper responses
            return None

        # Make sure we're not sending these in tests
        if settings.CHAHUB_API_URL and send:
            is_valid = self.get_chahub_is_valid()
            logger.info(f"ChaHub :: {self.__class__.__name__}({self.pk}) is_valid = {is_valid}")

            if is_valid:
                data = [self.clean_private_data(self.get_chahub_data())]

                data_hash = hashlib.md5(json.dumps(data).encode('utf-8')).hexdigest()
                # Send to chahub if we haven't yet, we have new data
                if not self.chahub_timestamp or self.chahub_data_hash != data_hash:
                    send_to_chahub.apply_async((self.app_label, self.pk, data, data_hash))
            elif self.chahub_needs_retry:
                # This is NOT valid but also marked as need retry, unmark need retry until this is valid again
                logger.info('ChaHub :: This is invalid but marked for retry. Clearing retry until valid again.')
                self.chahub_needs_retry = False
                super().save()

    def delete(self, send=True, *args, **kwargs):
        if send:
            self.deleted = True
            self.save(send=False)
            delete_from_chahub.apply_async((self.app_label, self.pk))
        else:
            super().delete(*args, **kwargs)
