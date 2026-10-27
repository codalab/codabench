from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0065_submission_resubmitted_from'),
    ]

    operations = [
        migrations.AddField(
            model_name='phase',
            name='max_submissions_scope',
            field=models.CharField(choices=[('participant', 'Participant'), ('organization', 'Organization')], default='participant', max_length=128),
        ),
    ]
