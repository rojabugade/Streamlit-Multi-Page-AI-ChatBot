import openai
import requests
import streamlit as st

# Function to get weather using the API key from secrets
def get_current_weather(location):
    # Retrieve the API key from Streamlit secrets
    API_key = st.secrets["open_Weather_Key"]
    
    if "," in location:
        location = location.split(",")[0].strip()
    
    # Construct the URL for the API request
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_key}"
    
    # Make the request to the API
    response = requests.get(url)
    
    # Check if the response status is 200 (OK)
    if response.status_code == 200:
        data = response.json()
        
        # Extract temperatures & Convert Kelvin to Celsius
        temp = data['main']['temp'] - 273.15
        feels_like = data['main']['feels_like'] - 273.15
        temp_min = data['main']['temp_min'] - 273.15
        temp_max = data['main']['temp_max'] - 273.15
        humidity = data['main']['humidity']
        
        # Return the extracted data
        return {
            "location": location,
            "temperature": round(temp, 2),
            "feels_like": round(feels_like, 2),
            "temp_min": round(temp_min, 2),
            "temp_max": round(temp_max, 2),
            "humidity": round(humidity, 2)
        }
    else:
        # If the API call fails, return None or an appropriate message
        return {"error": f"Failed to get weather data for {location}. Please check the location name and try again."}

# Function to get clothing suggestions from OpenAI based on the weather
def get_clothing_suggestions(weather_data):
    # Retrieve OpenAI API key from secrets
    openai_api_key = st.secrets["openai_api_key"]
    openai.api_key = openai_api_key
    
    # Construct the prompt for OpenAI
    prompt = (
        f"The current weather in {weather_data['location']} is as follows:\n"
        f"Temperature: {weather_data['temperature']}°C\n"
        f"Feels like: {weather_data['feels_like']}°C\n"
        f"Minimum Temperature: {weather_data['temp_min']}°C\n"
        f"Maximum Temperature: {weather_data['temp_max']}°C\n"
        f"Humidity: {weather_data['humidity']}%\n"
        "Based on this weather, what type of clothing would you suggest wearing today?"
    )
    
    # Call OpenAI API to get the suggestion using the latest model
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.5
        )
        suggestion = response['choices'][0]['message']['content'].strip()
        return suggestion
    except Exception as e:
        return f"An error occurred while generating suggestions: {e}"

def lab5_page():
    st.title("The What to Wear Bot")
    city_name = st.text_input("Enter a city name:", value="Syracuse, NY")
    
    if st.button("Get Suggestion"):
        # Get the weather data
        weather = get_current_weather(city_name)
        
        if "error" in weather:
            st.error(weather["error"])
        else:
            # Display the weather data
            st.write(weather)
            
            # Get clothing suggestions from OpenAI
            suggestion = get_clothing_suggestions(weather)
            st.write(f"Suggested clothing: {suggestion}")

