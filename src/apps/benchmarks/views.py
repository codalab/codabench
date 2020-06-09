from competitions.views import CompetitionManagement, CompetitionDetail, CompetitionForm, CompetitionUpload
from competitions.models import Competition


class BenchmarkManagement(CompetitionManagement):
    pass


class BenchmarkDetail(CompetitionDetail):
    pass


class BenchmarkForm(CompetitionForm):
    pass


class BenchmarkUpload(CompetitionUpload):
    queryset = Competition.objects.filter(competition_type=Competition.BENCHMARK)
