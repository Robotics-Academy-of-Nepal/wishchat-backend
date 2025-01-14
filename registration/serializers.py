from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'password']

    def create(self, validated_data):
        # Return a User instance
        return User.objects.create_user(**validated_data)

    def validate_username(self, value):
        # Add custom validation for username if needed
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError("Username and password are required.")

        # Authenticate the user using Django's built-in authentication
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        # Return the user object for further processing in the view
        data['user'] = user
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'has_active_chatbot','api_key', 'key_expiration_date']
        read_only_fields = ['username', 'email', 'has_active_chatbot', 'api_key', 'key_expiration_date']


class GoogleAuthSerializer(serializers.Serializer):
    auth_token = serializers.CharField()

class GoogleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 'has_active_chatbot']
        read_only_fields = ['id', 'username', 'email']

class APIKeySerializer(serializers.Serializer):
    duration_days = serializers.IntegerField()

    def validate_duration_days(self, value):
        if value <= 0:
            raise serializers.ValidationError("Duration must be a positive integer.")
        return value