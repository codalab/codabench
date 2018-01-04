from django.forms import ModelForm
from .models import Metric, Column, Leaderboard


class MetricForm(ModelForm):
    class Meta:
        model = Metric
        fields = '__all__'


class ColumnForm(ModelForm):
    class Meta:
        model = Column
        fields = '__all__'


class LeaderboardForm(ModelForm):
    class Meta:
        model = Leaderboard
        fields = '__all__'
