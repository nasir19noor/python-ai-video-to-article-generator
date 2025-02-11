from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
from pytube import YouTube
import os
import assemblyai as aai
import openai
import yt_dlp
from .models import BlogPost

# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data  ['link']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status=400)
        
        # get the video title
        title = yt_title(yt_link)

        # get the video transcript
        transcription = get_transription(yt_link)
        if not transcription:
            return JsonResponse({'error': 'Failed to get transcript'}, status=500)

        #Use openAI to generate the blog
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': 'Failed to generate blog article'}, status=500)
        
        #Save the blog to the database
        new_blog_article = BlogPost(
            user=request.user, 
            youtube_title=title, 
            youtube_link=yt_link, 
            generated_content=blog_content)
        new_blog_article.save()

        #return the blog article as a response
        return JsonResponse({'content': blog_content})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def yt_title(link):
    ydl_opts = {
        'noplaylist': True,  # Important: Only download single videos
        'quiet': True,       # Suppress console output
        'extract_flat': True, # Extract all formats
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)  # Don't download, just get info
            title = info_dict.get('title') # Get the title from info_dict
            if title:
                return title
            else:
                print("Title not found in info_dict")
                return "Untitled Video"
    except Exception as e:
        print(f"Error getting title: {e}")
        return "Untitled Video"

def download_audio(link):
    ydl_opts = {
        'format': 'bestaudio/best',  # Choose the best audio quality
        'outtmpl': os.path.join(settings.MEDIA_ROOT, '%(title)s.%(ext)s'), # Output path and filename template
        'noplaylist': True, # Only download single videos, not playlists
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(link, download=True)
        filename = ydl.prepare_filename(info_dict) # Get the actual filename after template substitution

    return filename

def get_transription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = ""

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)

    return transcript.text 

def generate_blog_from_transcription(transcription):
    openai.api_key = ""  # Make absolutely sure to replace this!

    messages = [
        {"role": "system", "content": "You are a helpful assistant that generates blog articles from YouTube video transcripts."},
        {"role": "user", "content": f"Based on the following transcript from a Youtube video, write a comprehensive blog article, write it based it based on the transcript, but don't make it look a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"}
    ]

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",  # Or gpt-4 if you have access and want to use it
        messages=messages,
        max_tokens=1000
    )

    generated_content = response.choices[0].message.content.strip()

    return generated_content

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = 'Invalid credentials'
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword'] 
        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating user'
                return render(request, 'signup.html', {'error_message': error_message})
        else:
            error_message = 'Password do not match'
            return render(request, 'signup.html', {'error_message': error_message}) 
          
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')
