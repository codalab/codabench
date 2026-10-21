from django.core.management.base import BaseCommand
from competitions.models import Competition
from competitions.tagging import auto_tag_competition, get_default_classifiers


class Command(BaseCommand):
    help = "Auto-tags competitions using configured tag classifiers."

    def add_arguments(self, parser):
        parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            dest="rerun_all",
            help="Rerun auto-tagging on all competitions, including those that already have tags",
        )

    def handle(self, *args, **options):
        rerun_all = options.get("rerun_all", False)

        if rerun_all:
            competitions = Competition.objects.all()
            print(f"Running auto-tagging on all {competitions.count()} competition(s) (including tagged)...")
        else:
            competitions = Competition.objects.filter(tags__isnull=True).distinct()
            print(f"Running auto-tagging on {competitions.count()} untagged competition(s)...")

        # Pre-load classifiers once to avoid reloading weights per competition
        classifiers = get_default_classifiers()
        tagged_count = 0
        for comp in competitions:
            tags = auto_tag_competition(comp.id, overwrite=rerun_all, classifiers=classifiers)
            if tags:
                tagged_count += 1
                tag_names = [f"{t.category.name}: {t.name}" for t in tags]
                comp_title = (comp.title or "")[:40]
                print(f"Competition {comp.id} ('{comp_title}'): tagged with {tag_names}")

        print(f"Finished auto-tagging. {tagged_count} competition(s) tagged.")
