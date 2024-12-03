"""
Flask application that integrates with Spotify and OpenAI APIs to provide personalized content based on the user's Spotify data.

Features:
- User authentication with Spotify
- Display user's top tracks and artists
- Display recently played tracks
- Generate an image prompt based on user's top tracks and create an image using DALL-E
- Provide song recommendations using OpenAI's GPT model
"""

from flask import Flask, request, redirect, render_template, session, url_for
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
from datetime import datetime
from tzlocal import get_localzone
import json

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Set up Spotify credentials
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

# Set up OpenAI API key
client=OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

# Set up Spotify OAuth
spotify_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope='user-top-read user-read-recently-played',
    show_dialog=True
)

@app.route("/")
def index():
    """Render the home page."""
    spotify_token = get_spotify_token()
    logged_in = spotify_token is not None
    return render_template("index.html", logged_in=logged_in)

@app.route("/sign-in")
def sign_in():
    """Initiate Spotify sign-in process."""
    # Get the authorization URL from SpotifyOAuth
    auth_url = spotify_oauth.get_authorize_url()
    session["spotify_token"] = spotify_oauth.get_cached_token()

    # Redirect the user to Spotify's authorization page
    return redirect(auth_url)

@app.route("/sign-out")
def sign_out():
    """Sign out the user by clearing the session."""
    # Clear all session data, including spotify_token
    session.clear()
    return redirect(url_for("index"))

@app.route("/callback")
def callback():
    """Handle Spotify OAuth callback."""
    # Check if 'code' is in the request arguments
    if 'code' not in request.args:
        # Redirect to the home page if authorization was canceled
        session.clear()
        return redirect(url_for("index"))
    
    # Get token using authorization code
    spotify_token = spotify_oauth.get_access_token(request.args['code'])
    session["spotify_token"] = spotify_token
    # Redirect to the stored URL or index if none
    next_url = session.pop("next_url", None)  # Remove from session after use
    return redirect(next_url or url_for("index"))

@app.route("/display-top-tracks")
def display_top_tracks():
    """Display user's top tracks."""
    spotify_token = get_spotify_token()
    if not spotify_token:
        session["next_url"] = request.url
        return redirect(url_for("sign_in"))
    
    top_tracks_info = get_top_tracks(spotify_token)
    return render_template("tracks-result.html", tracks=top_tracks_info)

@app.route("/display-top-artists")
def display_top_artists():
    """Display user's top artists."""
    spotify_token = get_spotify_token()
    if not spotify_token:
        session["next_url"] = request.url
        return redirect(url_for("sign_in"))
    
    top_artists = get_top_artists(spotify_token)
    return render_template("top-artists-result.html", artists=top_artists)

@app.route("/display-recently-played")
def display_recently_played():
    """Display user's recently played tracks."""
    spotify_token = get_spotify_token()
    if not spotify_token:
        session["next_url"] = request.url
        return redirect(url_for("sign_in"))
    
    recently_played = get_recently_played(spotify_token)
    return render_template("recently-played-result.html", tracks=recently_played)

@app.route("/display-image")
def display_image():
    """Generate and display an image based on user's top tracks."""
    spotify_token = get_spotify_token()
    if not spotify_token:
        session["next_url"] = request.url
        return redirect(url_for("sign_in"))
    
    prompt = generate_dalle_prompt(spotify_token)
    image_url = generate_dalle_image(prompt)
    return render_template("image-result.html", prompt=prompt, image_url=image_url)

@app.route("/display-recommended-songs")
def display_recommended_songs():
    """Display recommended songs based on user's top tracks."""
    spotify_token = get_spotify_token()
    if not spotify_token:
        session["next_url"] = request.url
        return redirect(url_for("sign_in"))
    recommended_tracks = get_song_recommendations(spotify_token)
    return render_template("tracks-result.html", tracks=recommended_tracks)

def get_spotify_token():
    """Retrieve and refresh Spotify token if necessary."""
    spotify_token = session.get("spotify_token", None)
    if not spotify_token:
        return None
    if spotify_oauth.is_token_expired(spotify_token):
        spotify_token = spotify_oauth.refresh_access_token(spotify_token['refresh_token'])
        session["spotify_token"] = spotify_token
    return spotify_token

def get_top_tracks(spotify_token):
    """Retrieve user's top tracks from Spotify."""
    sp = spotipy.Spotify(auth=spotify_token['access_token'])

    # Get user's top 50 tracks
    user_top_tracks = sp.current_user_top_tracks(limit=50, time_range='short_term')
    user_top_tracks_info = [
        f"{idx + 1}\t{item['album']['images'][0]['url']}\t{item['name']}\t{', '.join(artist['name'] for artist in item['artists'])}" 
        for idx, item in enumerate(user_top_tracks['items'])
    ]

    return user_top_tracks_info

def get_top_artists(spotify_token):
    """Retrieve user's top artists from Spotify."""
    sp = spotipy.Spotify(auth=spotify_token['access_token'])

    user_top_artists = sp.current_user_top_artists(limit=50, time_range='short_term')
    user_top_artists_info = [
        f"{idx + 1}.\t{item['images'][0]['url']}\t{item['name']}"
        for idx, item in enumerate(user_top_artists['items'])
    ]

    return user_top_artists_info

def get_recently_played(spotify_token):
    """Retrieve user's recently played tracks from Spotify."""
    sp = spotipy.Spotify(auth=spotify_token['access_token'])
    
    user_recently_played = sp.current_user_recently_played(limit=50)
    user_recently_played_info = []

    # Automatically get the local timezone
    local_tz = get_localzone()

    for item in user_recently_played['items']:
        track_name = item['track']['name']
        artist_name = ", ".join(artist['name'] for artist in item['track']['artists'])
        played_at_iso = item['played_at']

        # Convert ISO 8601 timestamp to UTC datetime
        played_at_utc = datetime.fromisoformat(played_at_iso.replace('Z', '+00:00'))
        # Convert UTC to the local timezone
        played_at_local = played_at_utc.astimezone(local_tz)
        formatted_time = played_at_local.strftime("%m/%d/%Y, %I:%M %p")

        user_recently_played_info.append(f"{track_name}\t{artist_name}\t{formatted_time}")

    return user_recently_played_info

def generate_dalle_prompt(spotify_token):
    """Generate a DALL-E prompt based on user's top tracks."""
    sp = spotipy.Spotify(auth=spotify_token['access_token'])

    # Get user's top 50 tracks
    user_top_5_tracks = sp.current_user_top_tracks(limit=5, time_range='short_term')

    image_tracks_list = [
        f"{item['name']} by {', '.join(artist['name'] for artist in item['artists'])}" 
        for idx, item in enumerate(user_top_5_tracks['items'])
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
            "role": "system",
            "content": "You are an AI assistant specializing in creating detailed and imaginative prompts for DALL-E to generate an image based on given song lists."
            },
            {
            "role": "user",
            "content": f"Create a prompt for an image that combines elements inspired by the themes, lyrics, mood, genre, and cultural imagery of the following 5 songs:\n{image_tracks_list}. Do not include the song titles or artists in the description"
            }
        ],
    )

    return response.choices[0].message.content


def generate_dalle_image(prompt):
    """Generate an image using DALL-E based on the given prompt."""
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size='1024x1024',
        n=1,
    )
    image_url=response.data[0].url
    return image_url

def get_song_recommendations(spotify_token):
    """Generate song recommendations based on user's top tracks."""
    sp = spotipy.Spotify(auth=spotify_token['access_token'])

    user_top_tracks = sp.current_user_top_tracks(limit=50, time_range='short_term')
    user_top_tracks_info = [
        f"{item['name']} by {', '.join(artist['name'] for artist in item['artists'])}" 
        for item in user_top_tracks['items']
    ]

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system", 
                "content": "You analyze user data and generate a JSON response containing music tracks based on user preferences."
            },
            {
                "role": "user", 
                "content": (
                    f"Based on my top Spotify songs, {user_top_tracks_info} provide a list of 10 recommended tracks. Each track should include its name and the artist's name."
                )
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "track_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "tracks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "track_name": {
                                        "description": "The name of the track",
                                        "type": "string"
                                    },
                                    "artist_name": {
                                        "description": "A comma-separated list of all artist names for the track",
                                        "type": "string"
                                    },
                                    "additionalProperties": False
                                }
                            }
                        },
                        "additionalProperties": False
                    }
                }
            }
        }
    )

    recommended_tracks = json.loads(response.choices[0].message.content)

    recommended_tracks_info = []
    for idx, track in enumerate(recommended_tracks['tracks'], start=1):
        query = f"{track['track_name']} {track['artist_name']}" 
        suggested_song = sp.search(q=query, type='track')['tracks']['items'][0]
        # Track title
        track_title = suggested_song['name']
        
        # Artist name(s)
        artist_names = ', '.join(artist['name'] for artist in suggested_song['artists'])
        
        # Album image URL (typically the first/largest image)
        track_image_url = suggested_song['album']['images'][0]['url']
        recommended_tracks_info.append(f"{idx}\t{track_image_url}\t{track_title}\t{artist_names}")

    return recommended_tracks_info

if __name__ == "__main__":
    app.run(debug=True, port=8888)
