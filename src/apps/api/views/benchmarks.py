from .competitions import CompetitionViewSet, CompetitionCreationTaskStatusViewSet
from competitions.models import Competition


class BenchmarkViewSet(CompetitionViewSet):
    queryset = Competition.objects.filter(type=Competition.BENCHMARK)


class BenchmarkCreationTaskStatusViewSet(CompetitionCreationTaskStatusViewSet):
    pass
