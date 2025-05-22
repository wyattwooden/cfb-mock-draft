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

class Position(models.Model):
    position_name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=10)

    def __str__(self):
        return self.abbreviation

class Player(models.Model):
    player_name = models.CharField(max_length=100)
    team = models.ForeignKey(CollegeTeam, on_delete=models.SET_NULL, null=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True)
    jersey = models.IntegerField(blank=True, null=True)
    class_year = models.CharField(max_length=20, blank=True, null=True)
    player_url = models.URLField(max_length=300, blank=True)
    player_stats_url = models.URLField(max_length=300, blank=True)

    def __str__(self):
        return self.player_name
