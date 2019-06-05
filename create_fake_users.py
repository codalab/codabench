from datetime import datetime
from random import randint, choice
import string


def generate_random_sequence(length=8):
    letters = string.ascii_lowercase
    r =  ''.join(choice(letters) for c in range(length))
    return r

for i in range(400):
    unique_username = False
    username = None
    while not unique_username:
        username = 'test_user_' + str(generate_random_sequence())
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            unique_username = True

    u = User.objects.create_user(username, password='test')
    u.date_joined = datetime(2010 + randint(0,8), randint(1,12), randint(1,28),2,2,2,0)
    u.email = username + '@test_email.com'
    u.save()
