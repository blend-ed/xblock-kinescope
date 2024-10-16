"""
Helpers functions for Kinescope XBlock
"""
from django.core.exceptions import ValidationError
from urllib.parse import urlparse

import json
import requests


def _(text):
    """
    Make '_' a no-op so we can scrape strings
    """
    return text


def validate_parse_kinescope_url(text):
    """
    Check if given text is valid kinescope video url and extract
    video id from it.
    """
    parsed_url = urlparse(text)
    if parsed_url.scheme == "https" and parsed_url.netloc == "kinescope.io":
        return parsed_url.path.split('/')[-1]
    else:
        raise ValidationError(_("Provided Kinescope Video URL is invalid"))
    


def kinescope_list_videos(api_key):
    """
    List all videos from Kinescope account
    """
    # curl https://api.kinescope.io/v1/videos \                           
    # -H 'Authorization: Bearer 97183963-55ef-431e-a17f-7466be4a9b1c'
    headers = {
        'Authorization': f'Bearer {api_key}'
    }

    response = requests.get('https://api.kinescope.io/v1/videos?per_page=1000', headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def get_video_list(api_key):
    """
    Get video list from Kinescope
    """
    video_data = kinescope_list_videos(api_key)
    video_list = []
    for video in video_data['data']:
        video_list.append({
            'title': video['title'],
            'play_link': video['play_link'],
        })

    return video_list