!!! note "This intervention is needed when upgrading from a version equal or lower than [v1.4.1](https://github.com/codalab/codabench/releases/tag/v1.4.1)"

In order to create a "logo icon" for each existing competition

1. Shell into django
```bash
docker compose exec django bash
python manage.py shell_plus --plain
```

2. Get competitions that don't have logo icons
```python
import io, os
from PIL import Image
from django.core.files.base import ContentFile
comps_no_icon_logo = Competition.objects.filter(logo_icon__isnull=True)
all = Competition.objects.all()
len(Competition.objects.all())
len(comps_no_icon_logo)
```

3. Then run this script
```python
for comp in comps_no_icon_logo:
    try:
        comp.make_logo_icon()
        comp.save()
    except Exception as e:
        print(f"An error occurred: {e}")
        print(comp)
```
