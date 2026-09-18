from django.db import migrations


def create_service_accounts_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='service_accounts')


def remove_service_accounts_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='service_accounts').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0024_remove_user_is_bot'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_service_accounts_group, remove_service_accounts_group),
    ]
