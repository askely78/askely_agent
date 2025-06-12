from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
from langdetect import detect
from openai import OpenAI
import requests

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔧 Fonction météo connectée à OpenWeatherMap
def get_weather(city):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=fr"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("cod") != 200:
            return f"Je n'ai pas pu trouver la météo pour {city}."
        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"La météo à {city} est actuellement : {weather}, avec une température de {temp}°C."
    except Exception:
        return "Une erreur est survenue en récupérant la météo."

# 🔍 Détection d’intention (salutation, météo, recommandations, etc.)
def detect_intent(text):
    lowered = text.lower()
    if any(greet in lowered for greet in ["bonjour", "salut", "hello", "hi", "hey"]):
        return "greeting"
    if "météo" in lowered or "weather" in lowered:
        return "weather"
    if "recommande" in lowered or "recommend" in lowered or "hôtel" in lowered or "restaurant" in lowered:
        return "recommendation"
    return "chat"

# 💬 Présentation automatique selon la langue détectée
def get_intro_by_lang(lang):
    if lang.startswith("fr"):
        return "👋 Bonjour ! Je suis Askély, votre assistant intelligent multilingue. Je peux vous aider à trouver un hôtel, connaître la météo, comparer des services ou répondre à toutes vos questions. N’hésitez pas à me demander quoi que ce soit !"
    elif lang.startswith("en"):
        return "👋 Hello! I’m Askély, your intelligent multilingual assistant. I can help you find hotels, check the weather, compare services, or answer any questions. Just ask!"
    else:
        return "👋 Hello! I’m Askély, your assistant. I can help with travel, weather, recommendations and more!"

# 📲 Route du webhook WhatsApp
@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    lang = detect(incoming_msg)
    intent = detect_intent(incoming_msg)

    if intent == "greeting":
        answer = get_intro_by_lang(lang)

    elif intent == "weather":
        city = incoming_msg.split()[-1]
        answer = get_weather(city)

    elif intent == "recommendation":
        messages = [
            {"role": "system", "content": "Tu es Askély, un assistant intelligent qui recommande des lieux et services en fonction des besoins de l'utilisateur."},
            {"role": "user", "content": incoming_msg}
        ]
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages
        )
        answer = response.choices[0].message.content

    else:
        messages = [
            {"role": "system", "content": "Tu es Askély, un assistant IA multilingue qui répond naturellement aux questions."},
            {"role": "user", "content": incoming_msg}
        ]
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages
        )
        answer = response.choices[0].message.content

    reply = MessagingResponse()
    reply.message(answer)
    return str(reply)
