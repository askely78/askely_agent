from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os
from langdetect import detect

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    lang = detect(incoming_msg)
    
    messages = [{"role": "system", "content": "Tu es Askély, un assistant intelligent multilingue qui aide les gens dans toutes leurs demandes."},
                {"role": "user", "content": incoming_msg}]
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=messages
    )
    
    answer = response['choices'][0]['message']['content']
    reply = MessagingResponse()
    reply.message(answer)
    return str(reply)
