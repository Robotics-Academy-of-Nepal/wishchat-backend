from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny  
from playground.chatbot import query_assistant
from registration.models import User


@api_view(['POST'])
@permission_classes([AllowAny])
def chatbot_view(request):
    try:
        user_query = request.data.get('query')
        api_key = request.data.get('apiKey')
        print("the api key is: ", api_key)
        if not api_key or not user_query:
            return JsonResponse({
                'error': 'API key and query are required'
            }, status=400)
        
        try:
            user = User.objects.get(api_key=api_key)

            index_name = user.last_index_name

            response = query_assistant(user_query,index_name,temperature=0.7)

            return JsonResponse({'response': response}, status=200)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

