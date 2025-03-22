import requests
import json
from datetime import datetime, timedelta
import os

class ScoresService:
    def __init__(self, cache_duration=300):  # Cache for 5 minutes by default
        self.cache_file = 'data/scores_cache.json'
        self.cache_duration = cache_duration
    
    def get_tournament_scores(self):
        """
        Fetch tournament scores from ESPN's unofficial API
        Returns basic score data for display
        """
        # Check if cached data exists and is fresh
        if self._is_cache_valid():
            return self._read_cache()
        
        # Fetch new data from API
        try:
            # ESPN unofficial API for college basketball scoreboard
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
            
            # Optional: add parameters to filter for NCAA tournament
            # params = {'groups': '50'}  # 50 is NCAA tournament
            # response = requests.get(url, params=params)
            
            # Simplified version without filters to test
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                # Process the data to match your application's format
                processed_data = self._process_scores(data)
                # Cache the processed data
                self._write_cache(processed_data)
                return processed_data
            else:
                # If API request fails, return cached data even if expired
                return self._read_cache() or {"error": f"API returned status code {response.status_code}"}
        except Exception as e:
            print(f"Error fetching tournament scores: {str(e)}")
            # Return cached data in case of error
            return self._read_cache() or {"error": str(e)}
    
    def _process_scores(self, data):
        """Transform ESPN API response to a simplified format"""
        processed = {
            'last_updated': datetime.now().isoformat(),
            'games': []
        }
        
        # Process each game event from the ESPN data
        for event in data.get('events', []):
            # Extract competition data
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])
            
            # Only process if we have enough competitor data
            if len(competitors) >= 2:
                # Extract home and away teams (ESPN uses id '1' for away, '0' for home)
                home_team = next((team for team in competitors if team.get('homeAway') == 'home'), {})
                away_team = next((team for team in competitors if team.get('homeAway') == 'away'), {})
                
                # Create game object with relevant data
                game_data = {
                    'id': event.get('id', ''),
                    'date': event.get('date', ''),
                    'status': event.get('status', {}).get('type', {}).get('name', 'UNKNOWN'),
                    'home_team': home_team.get('team', {}).get('name', 'Unknown Team'),
                    'away_team': away_team.get('team', {}).get('name', 'Unknown Team'),
                    'home_score': home_team.get('score', '0'),
                    'away_score': away_team.get('score', '0'),
                    'period': competition.get('status', {}).get('period', 0),
                    'clock': competition.get('status', {}).get('displayClock', '')
                }
                processed['games'].append(game_data)
        
        return processed
    
    def _write_cache(self, data):
        """Write data to cache file"""
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        with open(self.cache_file, 'w') as f:
            json.dump(data, f)
    
    def _read_cache(self):
        """Read data from cache file"""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def _is_cache_valid(self):
        """Check if cache exists and is fresh"""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                last_updated = datetime.fromisoformat(data.get('last_updated'))
                return datetime.now() - last_updated < timedelta(seconds=self.cache_duration)
        except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError):
            return False 