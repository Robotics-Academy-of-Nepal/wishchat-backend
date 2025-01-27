from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from registration.models import MessageQuota, PaymentTransaction  # Import the new model
import base64
import json
from datetime import timedelta
from .authentication import APIKeyAuthentication
from django.utils import timezone

class PaymentSuccessView(APIView):
    authentication_classes = [APIKeyAuthentication]

    def post(self, request):
        # Extract the encoded data from the request
        encoded_data = request.data.get('data')
        if not encoded_data:
            return Response({'status': 'error', 'message': 'No data parameter received'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Decode the base64-encoded data
            decoded_data = base64.b64decode(encoded_data).decode('utf-8')
            payment_data = json.loads(decoded_data)

            # Log the decoded payment data
            print(f"Decoded payment data: {payment_data}")

            # Check if the payment status is "COMPLETE"
            if payment_data.get('status') != 'COMPLETE':
                return Response({'status': 'error', 'message': 'Payment not completed'}, status=status.HTTP_400_BAD_REQUEST)

            # Get the transaction ID
            transaction_id = payment_data.get('transaction_id')
            if not transaction_id:
                return Response({'status': 'error', 'message': 'Transaction ID not found in payment data'}, status=status.HTTP_400_BAD_REQUEST)

            # Get the user from the request (authenticated via API key)
            user = request.user

            # Check if the transaction ID already exists in the database
            if PaymentTransaction.objects.filter(transaction_id=transaction_id).exists():
                return Response({'status': 'error', 'message': 'Duplicate transaction ID'}, status=status.HTTP_400_BAD_REQUEST)

            # Get the payment amount
            total_amount = payment_data.get('total_amount')
            if not total_amount:
                return Response({'status': 'error', 'message': 'Total amount not found in payment data'}, status=status.HTTP_400_BAD_REQUEST)

            # Convert total_amount to an integer (remove commas and decimals if any)
            total_amount = int(float(total_amount.replace(',', '')))

            # Update the user's MessageQuota
            message_quota, created = MessageQuota.objects.get_or_create(user=user)
            message_quota.is_paid = True
            message_quota.is_trial = False
            message_quota.subscription_end_date = timezone.now() + timedelta(days=31)
            message_quota.messages_used = 0

            # Set the message limit based on the payment amount
            if total_amount == 5000:
                message_quota.message_limit = 5000
            elif total_amount == 7000:
                message_quota.message_limit = 7000
            elif total_amount == 10000:
                message_quota.message_limit = 10000
            else:
                return Response({'status': 'error', 'message': 'Invalid payment amount'}, status=status.HTTP_400_BAD_REQUEST)

            # Save the updated MessageQuota
            message_quota.save()

            # Save the transaction ID in the PaymentTransaction model
            PaymentTransaction.objects.create(user=user, transaction_id=transaction_id)

            return Response({'status': 'success', 'message': 'Subscription updated successfully'})

        except Exception as e:
            print(f"Error processing payment: {str(e)}")
            return Response({'status': 'error', 'message': 'Error processing payment'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)