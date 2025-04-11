from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Chat

from google import genai

client = genai.Client(api_key="AIzaSyDKXxTejWpywjw6OTB7YAhb7QXAjGSP2wg")

def ask_gemini(message, display_name="User"):
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=f"You are talking to {display_name}, a curious book/games/movies lover. They ask: {message}"
    )
    return response.text

def ask_gemini_recommendations(message, list_of_liked_media, type_of_media):
    if len(list_of_liked_media) < 3:
        return "Please provide at least 3 liked media items for better recommendations."

    item_1, item_2, item_3 = list_of_liked_media[:3]

    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=f"You are talking to someone who enjoys {type_of_media}, particularly {item_1}, {item_2}, and {item_3}. "
                 "Give them 3 new recommendations of the same type of media given you know what they like. "
                 "Output it as just the names separated by a comma and no spaces (e.g. Harry Potter,Lord of the Rings,Focus)"
    )
    
    return response.text
