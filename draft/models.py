# draft/models.py
from django.db import models

class Conference(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class CollegeTeam(models.Model):
    team_name = models.CharField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=10, blank=True, null=True)
    conference = models.ForeignKey(Conference, on_delete=models.SET_NULL, null=True, blank=True)
    roster_url = models.URLField(max_length=300, blank=True)

    def __str__(self):
        return self.team_name

