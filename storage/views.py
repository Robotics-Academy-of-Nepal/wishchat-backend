from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .models import UserUpload
from .azure_upload import process_file
from .delete_index import delete_index_files
import os
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request):
    if request.method == 'POST':
        if 'file' in request.FILES and 'filename' in request.POST:
            uploaded_file = request.FILES['file']
            filename = request.POST['filename']
            print(filename)
            newfilename = filename.replace(" ","-").replace("(","").replace(")","")
            newfilename = newfilename.lower()
            # Check file extension
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']

            if file_extension not in allowed_extensions:
                return JsonResponse({'error': 'Invalid file type. Only PDF, DOC, DOCX, or TXT files are allowed.'}, status=400)

            try:
                index_name = os.path.splitext(newfilename)[0]  # Extract index name from filename

                # Process the file (upload to Azure)
                response_message = process_file(uploaded_file, index_name)

                # Save user upload info to the database
                user_upload = UserUpload(
                    user=request.user,
                    index_name=index_name  # Save the original index_name without modification
                )
                user_upload.save()

                request.user.has_active_chatbot = True
                request.user.last_index_name = index_name
                request.user.file_name = filename
                request.user.save()

                if response_message == "failed":
                    return JsonResponse({'error': 'File upload to Azure failed.'}, status=500)
                else:
                    # Print upload information to terminal
                    print(f"Upload saved - User: {user_upload.user.email}, Index Name: {user_upload.index_name}")
                    
                    return JsonResponse({
                        'message': 'File received and uploaded successfully!',
                        'filename': filename
                    }, status=200)

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'error': 'No file or filename provided.'}, status=400)

    return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_file(request):
    user = request.user

    try:
        index_name = user.last_index_name
        
        # Check if index_name exists before trying to delete
        if not index_name:
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        try:
            message = delete_index_files(index_name)
        except Exception as e:
            # Log the specific error from delete_index_files if needed
            print(f"Error deleting index files: {str(e)}")
            # Continue with user data cleanup even if index deletion fails
        
        # Clear user data regardless of index deletion success
        user.has_active_chatbot = False
        user.last_index_name = None
        user.file_name = ''
        user.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        return Response({
            "error": "Failed to clear user data",
            "details": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)