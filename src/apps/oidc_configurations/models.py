# oidc_configurations/models.py
from django.db import models


class Auth_Organization(models.Model):
    name = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    authorization_url = models.CharField(max_length=255)
    token_url = models.CharField(max_length=255)
    user_info_url = models.CharField(max_length=255)
    redirect_url = models.CharField(max_length=255)
    button_bg_color = models.CharField(max_length=20, default='#2C3E4C')
    button_text_color = models.CharField(max_length=20, default='#FFFFFF')
