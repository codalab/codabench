import datetime
from haystack import indexes
from .models import Competition


class CompetitionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    created_by = indexes.CharField(model_attr='created_by')
    created_when = indexes.DateTimeField(model_attr='created_when')

    def get_model(self):
        return Competition
