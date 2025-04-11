from datetime import datetime
import asyncio

from typing import AsyncGenerator
from django.shortcuts import render, redirect
from django.http import HttpRequest, StreamingHttpResponse, HttpResponse
from . import models
import json
from django.contrib.auth.decorators import login_required
from user_management.models import Profile

@login_required(login_url='login/')
def chat(request: HttpRequest) -> HttpResponse:
    return render(request, 'chat.html')

@login_required(login_url='login/')
def create_message(request: HttpRequest) -> HttpResponse:
    content = request.POST.get("content")
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if content:
        models.Message.objects.create(author=profile, content=content)
        return HttpResponse(status=201)
    else:
        return HttpResponse(status=200)

@login_required(login_url='login/')
async def stream_chat_messages(request: HttpRequest) -> StreamingHttpResponse:
    """
    Streams chat messages to the client as we create messages.
    """
    async def event_stream():
        """
        We use this function to send a continuous stream of data
        to the connected clients.
        """
        async for message in get_existing_messages():
            yield message

        last_id = await get_last_message_id()

        # Continuously check for new messages
        while True:
            new_messages = models.Message.objects.filter(id__gt=last_id).order_by('created_at').values(
                'id', 'author__display_name', 'content'
            )
            async for message in new_messages:
                yield f"data: {json.dumps(message)}\n\n"
                last_id = message['id']
            await asyncio.sleep(0.1)  # Adjust sleep time as needed to reduce db queries.

    async def get_existing_messages() -> AsyncGenerator:
        messages = models.Message.objects.all().order_by('created_at').values(
            'id', 'author__display_name', 'content'
        )
        async for message in messages:
            yield f"data: {json.dumps(message)}\n\n"

    async def get_last_message_id() -> int:
        last_message = await models.Message.objects.all().alast()
        return last_message.id if last_message else 0

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')