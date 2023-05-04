from statistics import mean
from django.db import models


class Leaderboard(models.Model):

    ADD = "Add"
    ADD_DELETE = "Add_And_Delete"
    ADD_DELETE_MULTIPLE = "Add_And_Delete_Multiple"
    FORCE_LAST = "Force_Last"
    FORCE_LATEST_MULTIPLE = "Force_Latest_Multiple"
    FORCE_BEST = "Force_Best"
    SUBMISSION_RULES = (
        (ADD, "Only allow adding one submission"),
        (ADD_DELETE, "Allow users to add a single submission and remove that submission"),
        (ADD_DELETE_MULTIPLE, "Allow users to add a multiple submissions and remove those submission"),
        (FORCE_LAST, "Force only the last submission"),
        (FORCE_LATEST_MULTIPLE, "Force latest submission to be added to leaderboard (multiple)"),
        (FORCE_BEST, 'Force only the best submission to the leaderboard')
    )

    AUTO_SUBMISSION_RULES = [FORCE_LAST, FORCE_BEST, FORCE_LATEST_MULTIPLE]

    primary_index = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=64)
    key = models.CharField(max_length=36)
    hidden = models.BooleanField(default=False)
    submission_rule = models.TextField(choices=SUBMISSION_RULES, default=ADD, null=False, blank=False)

    def __str__(self):
        return f'{self.title} - {self.id}'


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
    hidden = models.BooleanField(default=False)
    precision = models.IntegerField(default=2)

    class Meta:
        unique_together = ('leaderboard', 'key')
        ordering = ('index',)

    def __str__(self):
        return f'ID={self.id} - {self.title}'

    def compute(self, scores):
        return self.COMPUTATION_FUNCTIONS[self.computation](scores)


class SubmissionScore(models.Model):
    column = models.ForeignKey(Column, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=20, decimal_places=10)

    class Meta:
        ordering = ('column__index',)

    def __str__(self):
        return f'ID={self.id} - Column={self.column}'
