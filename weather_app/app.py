from flask import Flask, render_template, request

import requests

from urllib.parse import quote

from datetime import datetime

import psycopg2 as psy

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_url_path="/static")

# Retrieve environment variables
hostname = os.getenv("HOSTNAME")
database = os.getenv("DATABASE")
username = os.getenv("USER")
password = os.getenv("PASSWORD")
port = os.getenv("PORT_ID")
api_key = os.getenv("API_KEY")


class WeatherApp:
    def __init__(self):
        """Initialize WeatherApp with API key."""
        self.api_key = api_key


    @app.route("/")
    def index():
        """Render index.html template."""
        return render_template("index.html")


    @app.route("/weather", methods=['POST'])
    def weather():
        """Handle weather form submission."""
        city = request.form["city"]
        city_encoded = quote(city)

        # Fetch weather data from OpenWeatherMap API
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_encoded}&appid={WeatherApp().api_key}&units=metric"
        response = requests.get(url)
        data = response.json()

        # Process weather data
        if response.status_code == 200:
            weather_data = {
                "city": data["name"],
                "country": data.get("sys", {}).get("country", ""),  # Safely extract country information
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Include date in the timestamp
                "date": datetime.now().strftime("%Y-%m-%d")
            }

            # Connect to PostgreSQL database
            connection = psy.connect(
                dbname=database,
                port=port,
                user=username,
                password=password,
                host=hostname
            )
            cursor = connection.cursor()

            # Create table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_data (
                    id SERIAL PRIMARY KEY,
                    city VARCHAR(255) NOT NULL,
                    country VARCHAR(255) NOT NULL,
                    temperature REAL NOT NULL,
                    description VARCHAR(255) NOT NULL,
                    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date DATE
                )
            """)

            connection.commit()

            # Insert weather data into database
            cursor.execute(
                "INSERT INTO weather_data (city, country, temperature, description, time, date) VALUES (%s, %s, %s, %s, %s, %s)",
                (weather_data["city"], weather_data["country"], weather_data["temperature"], weather_data["description"], weather_data["time"], weather_data["date"])
            )

            connection.commit()

            cursor.close()

            connection.close()

            # Render weather.html template with weather data
            return render_template("weather.html", weather_data=weather_data)
        else:
            # Render error.html template if city not found
            return render_template("error.html", error_message="City not found")



if __name__ == "__main__":
    # Run the Flask app in debug mode
    app.run(debug=True)
