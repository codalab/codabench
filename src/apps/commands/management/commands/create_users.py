import os
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import get_random_string

from competitions.models import Competition, CompetitionWhiteListEmail
from profiles.forms import SignUpForm

User = get_user_model()

class Command(BaseCommand):
    BASE_DIR = Path("/app")
    IN_FILE_NAME = "users_to_create.txt"
    OUT_FILE_NAME = "created_users_data.txt"
    help = (
        "Create users from a list of emails and write the new data to a file. "
        "Optionally accept them to a competition. "
        f"Reads from '{IN_FILE_NAME}' in the project root directory. "
        f"Writes to '{OUT_FILE_NAME}' in the project root directory."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-c",
            "--competition",
            type=int,
            help="If a competition with this id exists, accept all created users to the competition",
        )

    def handle(self, *args, **options):
        in_path = self.BASE_DIR / self.IN_FILE_NAME
        if not os.path.exists(in_path):
            raise CommandError(f"File '{in_path}' doesn't exist")

        competition_id = options["competition"]
        try:
            competition = Competition.objects.get(pk=competition_id)
        except Competition.DoesNotExist:
            raise CommandError(f"Competition with id {competition_id} does not exist")
        self.stdout.write(f"Found competition '{competition.title}'")

        emails = []
        with open(in_path, "r") as f:
            for line in f:
                email = line.strip()
                if "@" in email: # very basic check
                    emails.append(email)
        self.stdout.write(f"Read {len(emails)} emails")

        # create and get users
        users_data = []
        for email in emails:
            username = email.split("@")[0]
            password = get_random_string(8)
            data = {
                "username": username,
                "email": email,
                "password1": password,
                "password2": password,
            }

            form = SignUpForm(data)
            if form.is_valid():
                form.save()
            else:
                self.stdout.write(f"{email}: {form.errors.as_data()}")

            try:
                user = User.objects.get(username=username)
                users_data.append((user, password))
            except User.DoesNotExist:
                self.stderr.write(f"Could not create or get a user for the email {email}")

        # write user data to file
        out_path = self.BASE_DIR / self.OUT_FILE_NAME
        with open(out_path, "w") as f:
            for data in users_data:
                user = data[0]
                password = data[1]
                f.write(f"{user.email} {user.username} {password}\n")
        self.stdout.write(f"\nWrote login data for {len(users_data)} users to file '{self.OUT_FILE_NAME}'")
        self.stdout.write("If an account already existed, the password in the output file will be incorrect")

        # create participation allowlist
        for email in emails:
            # prevents duplicates if already exists
            CompetitionWhiteListEmail.objects.update_or_create(competition=competition, email=email)

