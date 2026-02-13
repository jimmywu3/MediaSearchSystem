import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def get_movie_data():
    # get Genre List
    genre_url = f"{BASE_URL}/genre/movie/list?api_key={API_KEY}&language=en-US"
    genres = requests.get(genre_url).json().get('genres', [])
    
    all_movies = []

    # get all the genres
    for genre in genres:
        print(f"--- Processing Genre: {genre['name']} ---")
        discover_url = f"{BASE_URL}/discover/movie"
        params = {
            "api_key": API_KEY,
            "with_genres": genre['id'],
            "sort_by": "popularity.desc"
        }
        # limit to top 15 movies
        movie_results = requests.get(discover_url, params=params).json().get('results', [])[:15]
        
        for m in movie_results:
            movie_id = m['id']
            avg_rating = m.get('vote_average', 0.0)
            
            # fetch details and credits using append_to_response
            # gives runtime, overview, cast, and crew all at once
            detail_url = f"{BASE_URL}/movie/{movie_id}?api_key={API_KEY}&append_to_response=credits"
            full_data = requests.get(detail_url).json()
            
            # get runtime - returns length in minutes, default to 0 if not available
            runtime = full_data.get('runtime', 0)
            
            # get Director from the nested credits
            credits = full_data.get('credits', {})
            director = next((member['name'] for member in credits.get('crew', []) 
                            if member['job'] == 'Director'), "Unknown")
            
            # get Top 5 Actors
            actors = [member['name'] for member in credits.get('cast', [])][:5]
            
            movie_entry = {
                "tmdb_id": movie_id,
                "title": full_data.get('title'),
                "genre": genre['name'],
                "release_date": full_data.get('release_date', 'N/A'),
                "runtime": runtime,
                "avg_rating": avg_rating,
                "director": director,
                "actors": actors,
                "overview": full_data.get('overview', '')
            }
            
            all_movies.append(movie_entry)
            print(f"Fetched: {full_data.get('title')} | Runtime: {runtime}m | Dir: {director}")
            
            time.sleep(0.1)
            
    return all_movies

movie_data = get_movie_data()