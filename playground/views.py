from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated  # Change to IsAuthenticated
from storage.models import UserUpload
from .chatbot import query_assistant

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Require authentication
def get_latest_index_name(request):
    try:
        # Get the latest upload for the current user
        latest_upload = UserUpload.objects.filter(
            user=request.user
        ).order_by('-uploaded_at').first()  # Order by most recent

        if latest_upload:
            return JsonResponse({
                'index_name': latest_upload.index_name
            }, status=200)
        else:
            return JsonResponse({
                'error': 'No uploads found for this user.'
            }, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Require authentication
def handle_query(request):
    try:
        user_query = request.data.get('query')
        temperature = request.data.get('temperature')
        if not user_query:
            return JsonResponse({'error': 'No query provided.'}, status=400)

        # Get the latest index_name for the current user
        latest_upload = UserUpload.objects.filter(
            user=request.user
        ).order_by('-uploaded_at').first()


        if not latest_upload:
            return JsonResponse({
                'error': 'No uploads found for this user.'
            }, status=404)


        print("System prompt to be passed: ", request.user.system_prompt)
        # Use the latest index_name for the query
        response = query_assistant(user_query, latest_upload.index_name, request.user.system_prompt,temperature)
        return JsonResponse({'response': response}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setting_prompt(request):
    user = request.user
    prompt = request.data.get('prompt')
    try:
        user.system_prompt = prompt 
        user.save()
        print("User system Prompt: ", user.system_prompt)
        return JsonResponse({'message': 'System Prompt saved successfully.'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    