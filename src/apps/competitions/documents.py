from django_elasticsearch_dsl import DocType, Index, StringField
from .models import Competition

competitions = Index('competitions')
competitions.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@competitions.doc_type
class CompetitionDocument(DocType):
    class Meta:
        model = Competition

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'title',
            'created_when',
        ]

    created_by = StringField()

    def prepare_created_by(self, instance):
        return instance.created_by.username if instance.created_by else ""
