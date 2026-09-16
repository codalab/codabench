# profiles/management/commands/provision_worker_token.py
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Create an account for Compute Worker, this account is unusable (set_unusable_password)"

    def handle(self, *args, **options):
        User = get_user_model()
        token_path = os.environ.get('WORKER_TOKEN_FILE', '/run/secrets/worker_token')
        username = os.environ.get('WORKER_USERNAME', 'compute_worker')

        group, _ = Group.objects.get_or_create(name='service_accounts')

        worker, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@codabench.local', 'is_active': True},
        )
        if created:
            worker.set_unusable_password()
        worker.groups.add(group)
        worker.save()

        token, _ = Token.objects.get_or_create(user=worker)

        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, 'w') as f:
            f.write(token.key)
        os.chmod(token_path, 0o600)

        self.stdout.write(self.style.SUCCESS(f"Token worker prêt dans {token_path}."))
