import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from draft.models import CollegeTeam, Player, Position
import logging
import time
from urllib.parse import urljoin
import random
import re

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrapes player data from ESPN roster pages for all teams'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Delay between requests in seconds (default: 2.0)'
        )

    def clean_name_and_number(self, name_text):
        """Separate player name from jersey number"""
        match = re.search(r'^(.*?)(\d+)?$', name_text.strip())
        if match:
            name = match.group(1).strip()
            number = match.group(2) if match.group(2) else ''
            return name, number
        return name_text.strip(), ''

    def get_headers(self):
        """Return a dictionary of headers to mimic a browser request"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def extract_player_id(self, url):
        """Extract player ID from ESPN URL"""
        match = re.search(r'/_/id/(\d+)', url)
        return match.group(1) if match else None

    def get_stats_url(self, player_url):
        """Convert player profile URL to stats URL"""
        player_id = self.extract_player_id(player_url)
        if player_id:
            return f"https://www.espn.com/college-football/player/stats/_/id/{player_id}"
        return None

    def process_roster_table(self, table, team, positions, valid_positions):
        """Process a single roster table and return number of players added"""
        players_added = 0
        found_positions = set()

        for row in table.find_all('tr')[1:]:  # Skip header row
            try:
                cols = row.find_all('td')
                if len(cols) < 7:  # Ensure we have enough columns
                    continue
                    
                # Extract position from the correct column
                position = cols[2].text.strip()
                found_positions.add(position)
                
                if position not in valid_positions:
                    continue
                    
                # Extract name and jersey from the name column
                name_cell = cols[1]
                name_text = name_cell.text.strip()
                player_name, jersey = self.clean_name_and_number(name_text)
                
                # If jersey is empty, try to get it from the first column
                if not jersey:
                    jersey = cols[0].text.strip()
                
                # Get class/year
                class_year = cols[5].text.strip()
                
                # Get player URLs
                player_url = None
                player_stats_url = None
                
                # Find the player link in the name cell
                name_link = name_cell.find('a')
                if name_link and name_link.get('href'):
                    player_url = urljoin(team.roster_url, name_link['href'])
                    player_stats_url = self.get_stats_url(player_url)
                
                # Create or update player
                player, created = Player.objects.update_or_create(
                    player_name=player_name,
                    team=team,
                    defaults={
                        'position': positions[position],
                        'jersey': jersey,
                        'class_year': class_year,
                        'player_url': player_url,
                        'player_stats_url': player_stats_url
                    }
                )
                
                players_added += 1
                self.stdout.write(f"Processed: {player_name} ({position})")
                    
            except Exception as e:
                logger.error(f"Error processing player for {team.team_name}: {str(e)}")
                continue

        return players_added, found_positions

    def handle(self, *args, **options):
        delay = options['delay']
        # Update valid positions to include PK instead of K
        valid_positions = ['QB', 'RB', 'WR', 'TE', 'PK']
        
        # Create or get positions
        positions = {}
        for pos in valid_positions:
            # For PK position, store it as K in the database
            db_pos = 'K' if pos == 'PK' else pos
            position, created = Position.objects.get_or_create(
                abbreviation=db_pos,
                defaults={'position_name': db_pos}
            )
            positions[pos] = position

        teams = CollegeTeam.objects.filter(roster_url__isnull=False).exclude(roster_url='')
        
        for team in teams:
            self.stdout.write(f"\nProcessing {team.team_name}...")
            
            try:
                # Add delay between requests
                time.sleep(delay)
                
                headers = self.get_headers()
                response = requests.get(
                    team.roster_url,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all roster tables
                roster_tables = soup.find_all('table', {'class': 'Table'})
                
                if not roster_tables:
                    logger.warning(f"Could not find any roster tables for {team.team_name}")
                    continue
                
                total_players_added = 0
                all_found_positions = set()
                
                with transaction.atomic():
                    for table in roster_tables:
                        # Process each table
                        players_added, found_positions = self.process_roster_table(
                            table, team, positions, valid_positions
                        )
                        total_players_added += players_added
                        all_found_positions.update(found_positions)
                            
            except requests.RequestException as e:
                logger.error(f"Error fetching roster for {team.team_name}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing {team.team_name}: {str(e)}")
                continue
                
            # Print all positions found for this team
            self.stdout.write(f"\nPositions found for {team.team_name}:")
            self.stdout.write(f"Valid positions we're looking for: {valid_positions}")
            self.stdout.write(f"All positions found on roster: {sorted(all_found_positions)}")
            self.stdout.write(f"Added/updated {total_players_added} players for {team.team_name}")
                
        self.stdout.write(self.style.SUCCESS('\nSuccessfully completed player scraping')) 