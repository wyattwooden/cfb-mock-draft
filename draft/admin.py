# draft/admin.py
from django.contrib import admin
from django.core.management import call_command
from django.contrib import messages
from .models import CollegeTeam, Conference, Position, Player

@admin.register(CollegeTeam)
class CollegeTeamAdmin(admin.ModelAdmin):
    list_display = ("team_name", "abbreviation", "conference")
    actions = ['scrape_players']

    def scrape_players(self, request, queryset):
        try:
            call_command('scrape_players')
            self.message_user(request, "Successfully scraped player data", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error scraping players: {str(e)}", messages.ERROR)
    scrape_players.short_description = "Scrape players for selected teams"

@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("position_name", "abbreviation",)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("player_name", "position", "team", "class_year",)
    search_fields = ("player_name", "team__team_name", "position__abbreviation")
