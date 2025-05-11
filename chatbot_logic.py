import random
import nltk
import requests
import re
import json
import sqlite3
from textblob import TextBlob
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Load intents from data.json
with open('Intent_old.json', 'r', encoding='utf-8') as file:
    intents = json.load(file)['intents']  # Correcting here to fetch the 'intents' list from the JSON

# Prepare training data
X = []
y = []

# Loop through the intents and their responses
for intent_data in intents:
    intent = intent_data['intent']
    # Ensure we get the 'text' and 'responses' from each intent
    if 'text' in intent_data and 'responses' in intent_data:
        for text in intent_data['text']:  # Assuming 'text' holds the example inputs
            X.append(text)
            y.append(intent)

# Vectorization
vectorizer = TfidfVectorizer()
X_vectorized = vectorizer.fit_transform(X)

# Train model
model = LogisticRegression()
model.fit(X_vectorized, y)

# 🔄 Chatbot logic
def get_response(user_input, context=None):
    user_input = user_input.lower()

    # Analyze sentiment of user input
    sentiment_response = analyze_sentiment(user_input)  # Get sentiment-based response

    # Step 1: Joke API trigger
    if "joke" in user_input:
        return fetch_joke(), "tell me a joke"

    # Step 2: Weather handling
    if "weather" in user_input:
        match = re.search(r"in ([a-zA-Z\s]+)", user_input)
        if match:
            city = match.group(1)
            return fetch_weather(city), "what is the weather"
        else:
            return "Please specify a city. For example: 'What's the weather in Delhi?'", context

    # Step 3: Repeat context
    if "repeat" in user_input or "again" in user_input:
        if context:
            return f"As I said before: {context}", context
        else:
            return "There's nothing to repeat yet.", context

    # Step 4: Tell me more
    if "more" in user_input or "tell me more" in user_input:
        if context and context in intents:
            return random.choice([intent['responses'] for intent in intents if intent['intent'] == context][0]), context
        else:
            return "More about what?", context

    # Step 5: Predict intent
    user_input_vec = vectorizer.transform([user_input])
    prediction = model.predict(user_input_vec)[0]

    # Step 6: Return response based on intent prediction
    response = None
    for intent_data in intents:
        if intent_data['intent'] == prediction:
            response = random.choice(intent_data['responses'])
            break

    if response:
        # Combine the sentiment response with the actual intent-based response
        return f"{sentiment_response}", prediction

    return "Sorry, I didn't understand that. Can you rephrase?", context

# 🔸 Joke API function
def fetch_joke():
    try:
        response = requests.get("https://official-joke-api.appspot.com/random_joke")
        if response.status_code == 200:
            data = response.json()
            return f"{data['setup']} ... {data['punchline']}"
        else:
            return "Sorry, I couldn't get a joke at the moment."
    except Exception:
        return "Oops! Something went wrong while fetching a joke."

# 🔹 Weather API function
def fetch_weather(city):
    api_key = "0bdcc58e8f397dffc788ac25a3fa0764"  # Replace with your real key
    city = city.strip().title()
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "weather" in data and "main" in data:
            weather = data['weather'][0]['description'].capitalize()
            temperature = data['main']['temp']
            return f"The weather in {city} is {weather} with a temperature of {temperature}°C."
        else:
            return f"Sorry, I couldn't get full weather details for '{city}'."

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return f"Sorry, I couldn't find the weather for '{city}'."
        else:
            return f"HTTP error occurred: {http_err}"

    except Exception as e:
        return f"Something went wrong while fetching the weather: {str(e)}"

# 🔸 Translation using LibreTranslate
def translate_text_libre(text, target_language):
    url = "https://libretranslate.de/translate"
    params = {
        "q": text,
        "source": "auto",
        "target": target_language,
        "format": "text"
    }
    try:
        response = requests.post(url, data=params, timeout=5)
        response.raise_for_status()
        translated = response.json()
        return translated["translatedText"]
    except requests.exceptions.ConnectTimeout:
        return "Translation service timed out. Please try again later."
    except requests.exceptions.RequestException as e:
        return f"Translation error: {str(e)}"


def analyze_sentiment(text):
    # Create a TextBlob object
    blob = TextBlob(text)

    # Get the sentiment polarity and subjectivity
    sentiment = blob.sentiment

    # Polarity ranges from -1 (negative) to 1 (positive)
    # Subjectivity ranges from 0 (objective) to 1 (subjective)
    polarity = sentiment.polarity
    subjectivity = sentiment.subjectivity

    # Print the results
    print(f"Text: {text}")
    print(f"Sentiment Polarity: {polarity}")
    print(f"Sentiment Subjectivity: {subjectivity}")

    # Determine sentiment and generate appropriate response
    if polarity > 0:
        sentiment_label = "Positive"
        response = "Thank you for the kind words! 😊"
    elif polarity == 0:
        sentiment_label = "Neutral"
        response = "I see, what would you like to talk about?"
    else:
        sentiment_label = "Negative"
        response = "Sorry to hear that! How can I help improve your experience?"

    # Return the sentiment and response
    print(f"Sentiment: {sentiment_label}")
    print(f"Response: {response}")
    return response


# 🔸 Insert chat history into SQLite
def insert_chat_history(username, user_message, bot_response):
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()

    # Insert user message, bot response, and username into the table
    cursor.execute('''
        INSERT INTO chat_history (username, user_message, bot_response)
        VALUES (?, ?, ?)
    ''', (username, user_message, bot_response))

    conn.commit()
    conn.close()
    print("Chat history inserted successfully.")

# 🔹 Get chat history for a user
def get_chat_history(username):
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()

    cursor.execute("SELECT user_message, bot_response, timestamp FROM chat_history WHERE username = ? ORDER BY timestamp DESC", (username,))
    rows = cursor.fetchall()

    for row in rows:
        print(f"User: {row[0]}, Bot: {row[1]}, Time: {row[2]}")

    conn.close()

# Example usage for inserting chat history
insert_chat_history("user1", "Hello, bot!", "Hi there! How can I help you?")

# Example usage for getting chat history
get_chat_history("user1")

