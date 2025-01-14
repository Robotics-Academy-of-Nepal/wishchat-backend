from django.urls import path  
from .views import get_latest_index_name , handle_query , setting_prompt
  
urlpatterns = [  
    path('latest-index/', get_latest_index_name, name='get_index_name_by_session'),  
    path('query/', handle_query, name='handle_query'), 
    path('apply-changes/', setting_prompt, name='setting_prompt'), 

]   