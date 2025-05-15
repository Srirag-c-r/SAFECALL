from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from ..models import Message, Complaint, PublicUser, PoliceStation
from django.utils import timezone
import json

@login_required
def chat_room(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    messages = Message.objects.filter(complaint=complaint).order_by('timestamp')
    
    context = {
        'complaint': complaint,
        'messages': messages,
        'user': request.user,
    }
    return render(request, 'core/chat_room.html', context)

@login_required
def send_message(request, complaint_id):
    if request.method == 'POST':
        complaint = get_object_or_404(Complaint, id=complaint_id)
        content = request.POST.get('content')
        file = request.FILES.get('file')
        
        # Determine sender and receiver based on user type
        if isinstance(request.user, PublicUser):
            sender = request.user
            receiver = complaint.police_station
        else:
            sender = request.user
            receiver = complaint.user
            
        message = Message.objects.create(
            complaint=complaint,
            sender=sender,
            receiver=receiver,
            content=content,
            file=file
        )
        
        return JsonResponse({
            'status': 'success',
            'message_id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'sender_name': f"{sender.first_name} {sender.last_name}",
            'file_url': message.file.url if message.file else None
        })
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_messages(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    messages = Message.objects.filter(complaint=complaint).order_by('timestamp')
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'sender_name': f"{msg.sender.first_name} {msg.sender.last_name}",
        'is_read': msg.is_read,
        'file_url': msg.file.url if msg.file else None
    } for msg in messages]
    
    return JsonResponse({'messages': messages_data})

@login_required
def mark_message_read(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user == message.receiver:
        message.is_read = True
        message.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=403) 