# oidc_configurations/views.py
import base64
import requests
from django.shortcuts import render, redirect, get_object_or_404
from .models import Auth_Organization
from django.contrib.auth import get_user_model, login
import re

User = get_user_model()

BACKEND = 'django.contrib.auth.backends.ModelBackend'


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
                "response_type=code&"
                "scope=openid profile email&"
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

        try:
            # STEP 1: Get auth organization using its id
            organization = get_object_or_404(Auth_Organization, pk=auth_organization_id)

            if organization:

                # STEP 2:  Get access token
                access_token, token_error = get_access_token(organization, authorization_code)

                if token_error:
                    context["error"] = token_error
                else:
                    # STEP 3: Get user info
                    user_info, user_info_error = get_user_info(organization, access_token)
                    if user_info_error:
                        context["error"] = user_info_error
                    else:

                        # get email and nickname (username) of the user
                        user_email = user_info.get("email", None)
                        user_nickname = user_info.get("nickname", None)
                        if user_email:
                            # get user with this email
                            user = get_user_by_email(user_email)
                            # STEP 4: Check if user exists and user is created using oidc and oidc orgnaization matches this one
                            if user:
                                login(request, user, backend=BACKEND)
                                # Redirect the user home page
                                return redirect('pages:home')
                            else:
                                return register_and_authenticate_user(request, user_email, user_nickname, organization)

                        else:
                            context["error"] = "Unable to extract email from user info! Please contact platform"
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

    try:
        response = requests.request("POST", token_url, data=data, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        token_data = response.json()
        access_token = token_data.get('access_token')
        return access_token, None
    except requests.exceptions.RequestException as e:
        print(f"Error during token request: {e}")
        return None, e
    except Exception as e:
        print(f"Error parsing token response: {e}")
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


def register_and_authenticate_user(request, user_email, user_nickname, organization):

    if not user_nickname:
        username = re.sub(r'[^a-zA-Z0-9]', '', user_email.split('@')[0])
    else:
        username = user_nickname

    # Ensure the username is unique
    username = create_unique_username(username)

    # Create a new user
    user = User.objects.create(
        username=username,
        email=user_email,
        is_created_using_oidc=True,
        oidc_organization=organization,
    )

    if user:
        # login user
        login(request, user, backend=BACKEND)
        # Redirect to the home page
        return redirect('pages:home')

    else:
        # Handle authentication failure i.e. go back to login
        return redirect('accounts:login')


def create_unique_username(username):
    # Check if the username already exists
    if User.objects.filter(username=username).exists():
        # If the username already exists, modify it to make it unique
        suffix = 1
        new_username = f"{username}_{suffix}"
        while User.objects.filter(username=new_username).exists():
            suffix += 1
            new_username = f"{username}_{suffix}"
        return new_username
    else:
        # If the username doesn't exist, use it as is
        return username


def get_user_by_email(email):
    try:
        user = User.objects.get(email=email)
        return user
    except User.DoesNotExist:
        return None
