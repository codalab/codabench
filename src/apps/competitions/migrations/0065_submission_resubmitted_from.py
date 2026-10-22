from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0064_submission_selected_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='resubmitted_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resubmissions', to='competitions.submission'),
        ),
    ]
