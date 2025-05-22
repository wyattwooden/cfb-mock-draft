# draft/admin.py
from django.contrib import admin
from .models import CollegeTeam, Conference

@admin.register(CollegeTeam)
class CollegeTeamAdmin(admin.ModelAdmin):
    list_display = ("team_name", "abbreviation", "conference")

@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ("name",)
