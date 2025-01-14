from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer , GoogleAuthSerializer , GoogleUserSerializer
from .models import User
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid



class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            user.generate_api_key()  

            return Response({
                "message": "User registered successfully!",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful!",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "has_active_chatbot": user.has_active_chatbot  
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Delete the user's token to logout
            request.user.auth_token.delete()
            return Response({
                "message": "Successfully logged out."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": "Something went wrong when logging out."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("\n=== Starting Google Login Process ===")
        print("Received request data:", request.data)
        
        serializer = GoogleAuthSerializer(data=request.data)
        
        if not serializer.is_valid():
            print("Serializer validation failed:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        google_token = serializer.validated_data['auth_token']
        print("Retrieved token from request:", google_token[:20] + "..." if google_token else "None")
        
        try:
            print("Attempting to verify Google token with client ID:", settings.GOOGLE_OAUTH2_CLIENT_ID)
            # Verify the Google token
            idinfo = id_token.verify_oauth2_token(
                google_token, 
                requests.Request(), 
                settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            print("Token verification successful. User info:", idinfo)

            # Extract user info from Google response
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            print(f"Extracted user info - Email: {email}, First Name: {first_name}, Last Name: {last_name}")
            
            # Check if user exists
            try:
                print("Checking if user exists with email:", email)
                user = User.objects.get(email=email)
                print("Existing user found:", user.username)
            except User.DoesNotExist:
                print("User does not exist. Creating new user...")
                # Create new user if doesn't exist
                username = email.split('@')[0]  # Use email prefix as username
                base_username = username
                counter = 1
                
                # Handle username uniqueness
                while User.objects.filter(username=username).exists():
                    print(f"Username {username} already exists, trying {base_username}{counter}")
                    username = f"{base_username}{counter}"
                    counter += 1

                print("Creating new user with username:", username)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=None,  # Set unusable password for social auth
                    phone_number="",  # You might want to handle this differently
                )
                user.set_unusable_password()
                user.save()
                print("New user created successfully")

            
            if not user.api_key:
                # Generate a new API key with default duration (7 days)
                print("User does not have an API key. Generating a new one...")
                user.generate_api_key()  # This sets both the API key and its expiration date
                print(f"Generated API key: {user.api_key}, expires on: {user.key_expiration_date}")

            # Generate or get auth token
            print("Generating auth token for user:", user.username)
            token, _ = Token.objects.get_or_create(user=user)
            
            # Serialize user data
            user_serializer = GoogleUserSerializer(user)
            print("User serialized successfully")
            
    
            print("Company name: ",user.companyname)
            response_data = {
                "message": "Successfully logged in with Google",
                "token": token.key,
                "user": user_serializer.data,
                "api_key": user.api_key,
                "expiry date": user.key_expiration_date,
                "filename": user.file_name,
                "company_name": user.companyname,
                "google_data": {
                    "email": idinfo['email'],
                    "full_name": idinfo.get('name', ''),
                    "picture": idinfo.get('picture', ''),
                    "given_name": idinfo.get('given_name', ''),
                    "family_name": idinfo.get('family_name', ''),
                    "locale": idinfo.get('locale', '')
                }
            }
            print("=== Google Login Process Completed Successfully ===\n")
            return Response(response_data, status=status.HTTP_200_OK)

        except ValidationError as ve:
            print("Validation Error occurred:", str(ve))
            return Response({
                "error": "Invalid token",
                "detail": str(ve)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print("Unexpected error occurred:", str(e))
            print("Error type:", type(e).__name__)
            import traceback
            print("Full traceback:", traceback.format_exc())
            return Response({
                "error": str(e),
                "error_type": type(e).__name__
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CompanyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            companyname = request.data.get("company_name")
            if not companyname:
                return Response({"error": "Company name is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update the current user's company name
            user = request.user
            user.companyname = companyname
            user.save()
            
            return Response({"message": "Company name successfully registered"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)