from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from datetime import datetime, timedelta
import uuid

class UserManager(BaseUserManager):
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        if not email:
            raise ValueError('The Email field must be set')
        # if not phone_number:
        #     raise ValueError('The Phone Number field must be set')
        
        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(username, email, phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=15, unique=False, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    has_active_chatbot = models.BooleanField(default=False)
    last_index_name = models.CharField(max_length=50, null=True, blank=True)
    api_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    file_name = models.CharField(max_length=255,unique=False,null=False,blank=True)
    companyname = models.CharField(max_length=255,unique=False,null=False,blank=True)
    system_prompt = models.TextField(max_length=200000,null=True, unique=False,blank=True)
    key_expiration_date = models.DateTimeField(null=True, blank=True)
    objects = UserManager()
    
    USERNAME_FIELD = 'username'  
    REQUIRED_FIELDS = ['email', 'phone_number', 'first_name', 'last_name',]  
    
    def __str__(self):
        return self.username  
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        return self.is_superuser
    
    def generate_api_key(self, duration_days=7):
        """Generate a new API key and set an expiration date."""
        self.api_key = str(uuid.uuid4())
        self.key_expiration_date = datetime.now() + timedelta(days=duration_days)
        self.save()
        return self.api_key

    def extend_api_key(self, additional_days):
        """Extend the API key's expiration date."""
        if self.key_expiration_date:
            self.key_expiration_date += timedelta(days=additional_days)
        else:
            self.key_expiration_date = datetime.now() + timedelta(days=additional_days)
        self.save()

    def is_api_key_valid(self):
        """Check if the API key is valid."""
        return self.api_key and self.key_expiration_date > datetime.now()