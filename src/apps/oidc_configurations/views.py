# oidc_configurations/views.py
import base64
import http.client
import requests
from urllib.parse import urlparse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Auth_Organization


def organization_oidc_login(request):
    # Check if this is a post request and it contains organization_oauth2_login
    if request.method == 'POST' and 'organization_oidc_login' in request.POST:
        # Get auth organization id from the request
        auth_organization_id = request.POST.get('organization_oidc_login')

        # Get auth organization using its id
        organization = get_object_or_404(Auth_Organization, pk=auth_organization_id)

        if organization:
            # Create a redirect url consisiting of
            # - authorization_url
            # - client_id
            # - response_type
            # - redirect_uri
            oidc_auth_url = (
                f"{organization.authorization_url}?"
                f"client_id={organization.client_id}&"
                f"response_type=code&"
                f"redirect_uri={organization.redirect_url}"
            )

            # Redirect the user to the OIDC provider's authorization URL
            return redirect(oidc_auth_url)

    # Handle other cases or render a different template if needed
    return render(request, 'registration/login.html')


def oidc_complete(request, auth_organization_id):

    # create empty context
    context = {}

    # Get error or authorization code from the query string
    error = request.GET.get('error', None)
    error_description = request.GET.get('error_description', None)
    authorization_code = request.GET.get('code', None)

    if error:
        context["error"] = error

    if error_description:
        context["error_description"] = error_description

    # Token exhange process
    if authorization_code:

        print(f"\n\n\n Authentication Code: {authorization_code} \n\n\n")

        try:
            # STEP 1: Get auth organization using its id
            organization = get_object_or_404(Auth_Organization, pk=auth_organization_id)
            if organization:

                # Get access token
                access_token, token_error = get_access_token(organization, authorization_code)
                if token_error:
                    context["error"] = token_error

                print(f"\n\n\n Access Token: {access_token} \n\n\n")

                # STEP 2: Make a POST request to the user info endpoint to get user info
                user_info, user_info_error = get_user_info(organization, access_token)
                if user_info_error:
                    context["error"] = user_info_error

                print(f"\n\n\n User Info: {user_info} \n\n\n")

                print(user_info)
                # STEP 3: Check in db if this user exists then login, if user is new create a new user and then login

            else:
                context["error"] = "Invalid Organization ID!"
        except Exception as e:
            context["error"] = f"{e}"

    return render(request, 'oidc/oidc_complete.html', context)


def get_access_token(organization, authorization_code):

    token_url = organization.token_url
    client_id = organization.client_id
    client_secret = organization.client_secret
    redirect_url = organization.redirect_url

    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode("utf-8")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_header}",
    }
    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_url,
    }
    print("token url: ", token_url)
    print("data: ", data)
    print("header: ", headers)

    # response = requests.post(token_url, data=data, headers=headers)

    # try:
    #     token_data = response.json()
    #     return token_data.get('access_token'), None
    # except Exception as e:
    #     return None, e

    
    # try:
    #     response = requests.request("POST", token_url, data=data, headers=headers)
    #     response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
    #     token_data = response.json()
    #     access_token = token_data.get('access_token')
    #     return access_token, None
    # except requests.exceptions.RequestException as e:
    #     print(f"Error during token request: {e}")
    #     return None, e
    # except Exception as e:
    #     print(f"Error parsing token response: {e}")
    #     return None, e

    try:
        parsed_url = urlparse(token_url)
        conn = http.client.HTTPConnection(parsed_url.hostname, parsed_url.port)
        conn.request("POST", parsed_url.path, data, headers)
        response = conn.getresponse()
        token_data = response.read().decode("utf-8")
        access_token = token_data.get('access_token')
        conn.close()
        print("Response:", token_data)
        # Parse token_data if needed
        # access_token = ...
        return access_token, None
    except Exception as e:
        print(f"Error during token request: {e}")
        return None, e


def get_user_info(organization, access_token):

    user_info_url = organization.user_info_url

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(user_info_url, headers=headers)

    try:
        user_info = response.json()
        return user_info, None
    except Exception as e:
        return None, e
