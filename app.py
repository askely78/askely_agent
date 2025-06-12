from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
from langdetect import detect
from openai import OpenAI
import requests

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🌤 Fonction météo via OpenWeatherMap
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

# 🧠 Détection des intentions
def detect_intent(text):
    lowered = text.lower()
    if any(greet in lowered for greet in ["bonjour", "salut", "hello", "hi", "hey"]):
        return "greeting"
    if "météo" in lowered or "weather" in lowered:
        return "weather"
    if "recommande" in lowered or "recommend" in lowered or "hôtel" in lowered or "restaurant" in lowered:
        return "recommendation"
    if any(keyword in lowered for keyword in ["visiter", "tourisme", "à voir", "à faire", "guide", "lieux à", "monuments", "touristique"]):
        return "tourism"
    if any(keyword in lowered for keyword in ["programme", "circuit", "itinéraire", "planning", "jour par jour", "planning de visite"]):
        return "itinerary"
    return "chat"

# 👋 Présentation adaptée à la langue
def get_intro_by_lang(lang):
    if lang.startswith("fr"):
        return "👋 Bonjour ! Je suis Askély, votre assistant intelligent multilingue. Je peux vous aider à organiser votre voyage, découvrir les lieux à visiter, connaître la météo ou trouver les meilleures adresses locales."
    elif lang.startswith("en"):
        return "👋 Hello! I’m Askély, your smart multilingual assistant. I can help you discover tourist sites, check the weather, or find top local recommendations for your trip."
    else:
        return "👋 Hello! I’m Askély, your assistant. I can help with tourism, weather, recommendations and more!"

# 📲 Webhook WhatsApp
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
            {"role": "system", "content": "Tu es Askély, un assistant intelligent qui recommande des lieux, hôtels et restaurants en fonction des besoins de l'utilisateur."},
            {"role": "user", "content": incoming_msg}
        ]
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages
        )
        answer = response.choices[0].message.content

    elif intent == "tourism":
        messages = [
            {"role": "system", "content": "Tu es Askély, un guide touristique virtuel expert du Maroc et du monde. Quand un utilisateur demande des conseils touristiques, propose-lui des idées de visites, d’activités culturelles, de monuments, de balades typiques et de spécialités locales."},
            {"role": "user", "content": incoming_msg}
        ]
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages
        )
        answer = response.choices[0].message.content

    elif intent == "itinerary":
        messages = [
            {"role": "system", "content": "Tu es Askély, un expert en circuits touristiques internationaux. Quand un utilisateur te demande un itinéraire ou un circuit de voyage jour par jour, tu dois lui proposer un programme détaillé, adapté à la destination et à la durée du séjour."},
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
