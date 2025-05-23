import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from draft.models import Player
import logging
import time
from urllib.parse import urljoin
import re

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrapes ADP data from Fantasy Points for college football players'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Delay between requests in seconds (default: 2.0)'
        )

    def get_headers(self):
        """Return a dictionary of headers to mimic a browser request"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def handle(self, *args, **options):
        delay = options['delay']
        url = 'https://www.fantasypoints.com/cfb/adp#/'
        
        try:
            # Add delay between requests
            time.sleep(delay)
            
            headers = self.get_headers()
            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the ADP table
            adp_table = soup.find('table')
            
            if not adp_table:
                logger.warning("Could not find ADP table")
                return
            
            players_updated = 0
            
            with transaction.atomic():
                for row in adp_table.find_all('tr')[1:]:  # Skip header row
                    try:
                        cols = row.find_all('td')
                        if len(cols) < 5:  # Ensure we have enough columns
                            continue
                            
                        # Extract player data
                        player_name = cols[1].text.strip()
                        position = cols[2].text.strip()
                        team_name = cols[3].text.strip()
                        designation = cols[4].text.strip()  # Designation column
                        adp = cols[5].text.strip()  # OVR column
                        
                        # Try to find matching player in our database
                        try:
                            # First try exact match by name (including alternate names) and position
                            player = Player.objects.get(
                                Q(player_name__iexact=player_name) | 
                                Q(alternate_names__iexact=player_name),
                                position__abbreviation__iexact=position
                            )
                        except Player.DoesNotExist:
                            # If no exact match, try fuzzy matching
                            # Split alternate_names by comma and check each one
                            players = Player.objects.filter(
                                Q(player_name__icontains=player_name) |
                                Q(alternate_names__icontains=player_name),
                                position__abbreviation__iexact=position
                            )
                            
                            if players.count() == 1:
                                player = players.first()
                            else:
                                self.stdout.write(f"Could not find unique match for {player_name} ({position})")
                                continue
                        
                        # Convert ADP to float if possible
                        try:
                            adp_value = float(adp) if adp else None
                            if adp_value:
                                player.adp = adp_value
                                player.save()
                                players_updated += 1
                                self.stdout.write(f"Updated ADP for {player_name} ({position}): {adp_value}")
                        except (ValueError, TypeError):
                            self.stdout.write(f"Invalid ADP value for {player_name}: {adp}")
                            continue
                            
                    except Exception as e:
                        logger.error(f"Error processing player: {str(e)}")
                        continue
                        
        except requests.RequestException as e:
            logger.error(f"Error fetching ADP data: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            
        self.stdout.write(self.style.SUCCESS(f'Successfully updated ADP for {players_updated} players')) 