from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.models import User 
from user_library.models import UserLibraryItem
from user_management.models import Profile 
from .models import Chat

from google import genai
import markdown

def get_user_feedback_summary(user):
    try:
        feedback_items = UserLibraryItem.objects.filter(
            user=user
        ).select_related('media').exclude(
            rating__isnull=True, review__isnull=True, review__exact=''
        ).order_by('-last_updated')[:10] # Limit to recent 10 feedback items

        if not feedback_items:
            return None

        summary_parts = []
        for item in feedback_items:
            media_title = item.media.title if item.media else "an item"
            type = item.media.media_type if item.media else "media"
            entry = f"{media_title} ({type})"
            if item.rating:
                entry += f" rated {item.rating}/5"
            if item.review and item.review.strip():
                review_snippet = (item.review[:50] + '...') if len(item.review) > 50 else item.review
                entry += f", reviewed: \"{review_snippet}\""
            summary_parts.append(entry)

        if summary_parts:
            return "Recently rated/reviewed: " + "; ".join(summary_parts) + "."
        else:
            return None

    except Exception as e:
        print(f"Error fetching user feedback summary: {e}")
        return None

client = genai.Client(api_key="AIzaSyDKXxTejWpywjw6OTB7YAhb7QXAjGSP2wg") 

def ask_gemini(message, display_name="User", feedback_context=None):
    base_prompt = f"You are talking to {display_name}, a curious book/games/movies lover."
    if feedback_context:
        prompt = f"{base_prompt} {feedback_context} They ask: {message}"
    else:
        prompt = f"{base_prompt} They ask: {message}"

    print(f"--- Sending prompt to Gemini: ---\n{prompt}\n-------------------------------")


    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    
    return response.text
        

@login_required
def chatbot(request):
    chats = Chat.objects.filter(user=request.user).order_by('created_at') 

    if request.method == 'POST':
        message = request.POST.get('message')
        if not message:
             return JsonResponse({'error': 'Empty message received.'}, status=400)

        try:
            profile = request.user.profile
            display_name = profile.display_name or request.user.username
        except Profile.DoesNotExist:
            display_name = request.user.username
        except AttributeError:
             display_name = request.user.username

        user_feedback_context = get_user_feedback_summary(request.user)

        raw_response = ask_gemini(
            message,
            display_name=display_name,
            feedback_context=user_feedback_context
        )

        html_response = markdown.markdown(raw_response)

        Chat.objects.create(
            user=request.user,
            message=message,
            response=raw_response,
            created_at=timezone.now()
        )

        return JsonResponse({'message': message, 'response': html_response})

    return render(request, 'ai/chatbot.html', {'chats': chats})