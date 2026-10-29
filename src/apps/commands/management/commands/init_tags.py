from django.core.management.base import BaseCommand
from competitions.models import Tag, TagCategory
from competitions.default_tags import DEFAULT_TAXONOMY
from factories import TagFactory, TagCategoryFactory


class Command(BaseCommand):
    help = "Initializes default tag categories and tags"

    def add_arguments(self, parser):
        parser.add_argument(
            '-r',
            '--reset',
            action='store_true',
            help='Delete all tags and recreate default tag categories and tags'
        )

    def handle(self, *args, **kwargs):
        reset = kwargs.get('reset')

        if reset:
            print("Resetting tags and categories.")
            Tag.objects.all().delete()
            TagCategory.objects.all().delete()

        for category_name, tag_names in DEFAULT_TAXONOMY.items():
            category = TagCategoryFactory(name=category_name)
            for tag_name in tag_names:
                TagFactory(name=tag_name, category=category)

        total_categories = TagCategory.objects.count()
        total_tags = Tag.objects.count()
        print(f"Successfully added {total_categories} categories and {total_tags} tags to the database.")