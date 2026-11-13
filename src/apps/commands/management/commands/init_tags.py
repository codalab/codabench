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
            help='Delete all tags and recreate default taxonomy. WARNING: Clears all tags from all competitions!'
        )
        parser.add_argument(
            '--no-input',
            '--noinput',
            action='store_true',
            dest='no_input',
            help='Do not prompt for confirmation when resetting tags and categories',
        )

    def handle(self, *args, **kwargs):
        reset = kwargs.get('reset')
        no_input = kwargs.get('no_input')

        if reset:
            print(
                "WARNING: Resetting will delete ALL existing tags and categories\n"
                "Because tags are linked to competitions, this will also clear all assigned tags from ALL competitions in the database."
            )
            if not no_input:
                confirm = input("Are you sure you want to proceed? [y/N]: ").strip().lower()
                if confirm not in ("y", "yes"):
                    print("Reset aborted by user.")
                    return

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
