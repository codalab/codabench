from statistics import mean

from django.db import models


class Leaderboard(models.Model):
    # TODO: Check null and blank attributes
    competition = models.ForeignKey('competitions.Competition', on_delete=models.CASCADE, related_name="leaderboards",
                                    null=True, blank=True)
    primary_index = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=64)
    key = models.CharField(max_length=36)


class Column(models.Model):
    AVERAGE = 'avg'
    SUM = 'sum'
    MIN = 'min'
    MAX = 'max'
    COMPUTATION_CHOICES = (
        (AVERAGE, 'Average'),
        (SUM, 'Sum'),
        (MIN, 'Min'),
        (MAX, 'Max'),
    )
    SORTING = (
        ('desc', 'Descending'),
        ('asc', 'Ascending'),
    )

    COMPUTATION_FUNCTIONS = {
        AVERAGE: mean,
        SUM: sum,
        MIN: min,
        MAX: max,
    }

    computation = models.TextField(choices=COMPUTATION_CHOICES, null=True, blank=True)
    computation_indexes = models.TextField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=36)
    key = models.CharField(max_length=36)
    sorting = models.TextField(choices=SORTING, default=SORTING[0][0])
    index = models.PositiveIntegerField()
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name="columns")

    class Meta:
        unique_together = ('leaderboard', 'key')
        ordering = ('index',)

    def compute(self, scores):
        return self.COMPUTATION_FUNCTIONS[self.computation](scores)


class SubmissionScore(models.Model):
    column = models.ForeignKey(Column, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=20, decimal_places=10)

    class Meta:
        ordering = ('column__index',)
