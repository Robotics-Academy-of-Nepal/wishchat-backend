from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny  
from playground.chatbot import query_assistant
from registration.models import User, MessageQuota
from django.utils import timezone
import json
from .functions import sendwhatsapp_messages


VERIFY_TOKEN = 'd27260f9-0e18-4d9d-9a76-8039b5baa7c7'


@api_view(['POST'])
@permission_classes([AllowAny])
def chatbot_view(request):
    try:
        user_query = request.data.get('query')
        api_key = request.data.get('apiKey')

        if not api_key or not user_query:
            return JsonResponse({
                'error': 'API key and query are required'
            }, status=400)
        
        try:
            user = User.objects.get(api_key=api_key)
            quota, created = MessageQuota.objects.get_or_create(user=user)

            index_name = user.last_index_name
            prompt = user.system_prompt
            
            # Check subscription status first
            if not quota.is_trial and not quota.is_subscription_valid():
                quota.is_paid = False  # Subscription expired
                quota.save()
                return JsonResponse({
                    'error': 'Subscription expired. Please renew to continue.',
                    'subscription_expired': True
                }, status=403)

            # Check message quota
            if not quota.can_send_message():
                if quota.is_trial and not quota.is_trial_valid():
                    return JsonResponse({
                        'error': 'Trial period expired. Please upgrade to continue.',
                        'trial_expired': True
                    }, status=403)
                return JsonResponse({
                    'error': 'Message quota exceeded',
                    'quota_exceeded': True
                }, status=429)

            # Reset counter only if subscription is valid and it's a new month
            if quota.is_subscription_valid():
                current_month = timezone.now().month
                last_reset_month = quota.last_reset.month
                
                if current_month != last_reset_month:
                    quota.messages_used = 0
                    quota.last_reset = timezone.now()
                    quota.save()

            # Process message and increment counter
            response = query_assistant(user_query,index_name,prompt,temperature=0.7)
            quota.messages_used += 2
            quota.save()

            return JsonResponse({'response': response}, status=200)
            
        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid API key'}, status=401)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@api_view(['GET'])
@permission_classes([AllowAny])
def get_message_usage(request):
    api_key = request.headers.get('X-API-Key') or request.GET.get('api_key')
    
    if not api_key:
        return JsonResponse({
            'error': 'API key is required'
        }, status=400)
    
    try:
        user = User.objects.get(api_key=api_key)
        
        # Get or create message quota for the user
        quota, created = MessageQuota.objects.get_or_create(
            user=user,
            defaults={
                'messages_used': 0,
                'message_limit': 5000,
                'is_trial': True,
                'is_paid': False,
                'trial_start_date': timezone.now(),
                'last_reset': timezone.now()
            }
        )
        
        # Calculate remaining trial/subscription days
        days_remaining = None
        if quota.is_trial:
            trial_days_used = (timezone.now() - quota.trial_start_date).days
            days_remaining = max(0, 7 - trial_days_used)  # 7-day trial
        elif quota.is_subscription_valid():
            days_remaining = (quota.subscription_end_date - timezone.now()).days
        
        response_data = {
            'messages_used': quota.messages_used,
            'message_limit': quota.message_limit,
            'messages_remaining': max(0, quota.message_limit - quota.messages_used),
            'is_trial': quota.is_trial,
            'is_paid': quota.is_paid,
            'days_remaining': days_remaining,
            'last_reset': quota.last_reset,
            'status': 'active' if (quota.is_trial and quota.is_trial_valid()) or quota.is_subscription_valid() else 'inactive'
        }
        
        return JsonResponse(response_data, status=200)
        
    except User.DoesNotExist:
        return JsonResponse({
            'error': 'Invalid API key'
        }, status=401)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
    


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def whatsAppWebhook(request):
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)
        else:
            return HttpResponse('error', status=403)

    elif request.method == 'POST':
        try:
            # First, acknowledge receipt immediately
            data = json.loads(request.body)
            print("data:", data)
            # Safely extract data with proper validation
            entries = data.get('entry', [])
            whatsapp_id = data['entry'][0]['id']
            if not entries:
                return JsonResponse({"status": "success", "message": "No entries found"}, status=200)
                
            changes = entries[0].get('changes', [])
            if not changes:
                return JsonResponse({"status": "success", "message": "No changes found"}, status=200)
                
            value = changes[0].get('value', {})
            messages = value.get('messages', [])
            
            if not messages:
                return JsonResponse({"status": "success", "message": "No messages found"}, status=200)
                
            message = messages[0]
            print(message)
            sender_wa_id = message.get('from')
            message_text = message.get('text', {})
            message_body = message_text.get('body') if message_text else None

            if not sender_wa_id or not message_body:
                return JsonResponse({"status": "success", "message": "Invalid message format"}, status=200)

            # Log the received message
            print(f"Message received from {sender_wa_id}: {message_body}")

            
            whatsapp_message = sendwhatsapp_messages(sender_wa_id, message_body,whatsapp_id)
            print("whatsapp_message:", whatsapp_message)
            return JsonResponse({"status": "success", "message": "Message processed"}, status=200)

        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {str(e)}")
            return JsonResponse({"status": "success", "message": "Invalid JSON"}, status=200)
            
        except Exception as e:
            print(f"Webhook Error: {str(e)}")
            return JsonResponse({"status": "success", "message": "Message received"}, status=200)