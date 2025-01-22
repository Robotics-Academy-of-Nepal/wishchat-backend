import requests
from registration.models import User

def sendwhatsapp_messages(phoneNumber, message, whatsapp_id):

    user = User.objects.get(whatsapp_id=whatsapp_id)
    whatsappurl = user.whatsapp_url
    whatsapptoken = user.whatsapp_token 
    apiKey = user.api_key
    query = message

    payload = {
        'apiKey': apiKey,
        'query': query
    }


    chatbot_response = requests.post(
        'http://127.0.0.1:8000/api/chat/',
        json=payload
    )

    bot_response = "No response generated"
    if chatbot_response.status_code == 200:
        response_data = chatbot_response.json()  # Properly parse the JSON response
        bot_response = response_data.get('response', bot_response)
        print("bot response:", bot_response)

    try:
        headers = {"Authorization": whatsapptoken}
        payload = {
            "messaging_product": 'whatsapp',
            "recipient_type": "individual",
            "to": phoneNumber,
            "type": "text",
            "text": {"body": bot_response}
        }

        response = requests.post(whatsappurl, headers=headers, json=payload)
        ans = response.json()
        return ans
    except Exception as e:
        print(f"Error sending WhatsApp message: {str(e)}")
        return {"error": str(e)}