from rest_framework import serializers


class AnalyticsSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    time_unit = serializers.CharField(max_length=5, required=False)
    registered_user_count = serializers.IntegerField(required=False)
    competition_count = serializers.IntegerField(required=False)
    competitions_published_count = serializers.IntegerField(required=False)
    submissions_made_count = serializers.IntegerField(required=False)
    users_data_date = serializers.DateField(required=False)
    users_data_count = serializers.IntegerField(required=False)
    competitions_data_date = serializers.DateField(required=False)
    competitions_data_count = serializers.IntegerField(required=False)
    submissions_data_date = serializers.DateField(required=False)
    submissions_data_count = serializers.IntegerField(required=False)
