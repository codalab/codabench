from datetime import datetime
from random import randint, choice
import string


def generate_random_sequence(length=8):
    letters = string.ascii_lowercase
    r =  ''.join(choice(letters) for c in range(length))
    return r

users = User.objects.all()
user_count = User.objects.count()

for i in range(1000):
    unique_title = False
    title = None
    while not unique_title:
        title = 'test_competition_' + str(generate_random_sequence())
        try:
            comp = Competition.objects.get(title=title)
        except Competition.DoesNotExist:
            unique_title = True

    u = users[randint(0,user_count - 1)]
    created_when = datetime(2010 + randint(0,8), randint(1,12), randint(1,28),2,2,2,0)
    print(created_when)
    c = Competition.objects.create(title=title, created_when=created_when, created_by=u)
    c.published = randint(0,1) == 0
    c.save()
