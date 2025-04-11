from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from user_management.models import Profile
from .models import Chat

from google import genai
import markdown 

client = genai.Client(api_key="AIzaSyDKXxTejWpywjw6OTB7YAhb7QXAjGSP2wg")

def ask_gemini(message, display_name="User"):
    response = client.models.generate_content(
    	model="gemini-2.0-flash", contents= f"You are talking to {display_name}, a curious book/games/movies lover. They ask: {message}"
	)
    return response.text

@login_required
def chatbot(request):
    chats = Chat.objects.filter(user=request.user)

    if request.method == 'POST':
        message = request.POST.get('message')

        try:
            profile = request.user.profile
            display_name = profile.display_name or request.user.username
        except Profile.DoesNotExist:
            display_name = request.user.username

        raw_response = ask_gemini(message, display_name=display_name)

        html_response = markdown.markdown(raw_response)

        Chat.objects.create(
            user=request.user,
            message=message,
            response=raw_response,
            created_at=timezone.now()
        )

        return JsonResponse({'message': message, 'response': html_response})

    return render(request, 'ai/chatbot.html', {'chats': chats})
