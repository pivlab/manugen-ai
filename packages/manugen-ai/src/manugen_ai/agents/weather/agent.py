import datetime
from zoneinfo import ZoneInfo

import requests
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """

    common_headers = {"User-Agent": "ManugenAI Weather Agent"}

    try:
        # Geocode the city using OpenStreetMap Nominatim API
        geocode_url = "https://nominatim.openstreetmap.org/search"
        geocode_params = {"q": city, "format": "json", "limit": 1}
        geocode_response = requests.get(
            geocode_url, params=geocode_params, headers=common_headers
        )
        geocode_response.raise_for_status()
        geocode_data = geocode_response.json()

        if not geocode_data:
            return {"status": "error", "error_message": f"City '{city}' not found"}

        lat = float(geocode_data[0]["lat"])
        lon = float(geocode_data[0]["lon"])

        # Get weather data using Open-Meteo API
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "timezone": "auto",
            "temperature_unit": "fahrenheit",
        }
        weather_response = requests.get(
            weather_url, params=weather_params, headers=common_headers
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        current = weather_data["current"]
        report = (
            f"Current weather in {city}: "
            f"Temperature: {current['temperature_2m']}°F, "
            f"Humidity: {current['relative_humidity_2m']}%, "
            f"Wind Speed: {current['wind_speed_10m']} km/h"
        )

        return {"status": "success", "report": report}

    except requests.RequestException as e:
        return {"status": "error", "error_message": f"API request failed: {str(e)}"}
    except (KeyError, IndexError, ValueError) as e:
        return {
            "status": "error",
            "error_message": f"Error parsing API response: {str(e)}",
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def get_current_time(city: str, tz_identifier: str) -> dict:
    """Returns the current time in a specified city in the specified country.

    Args:
        city (str): The name of the city for which to retrieve the current time.
        tz_identifier (str): The timezone identifier, e.g., "America/New_York".

    Returns:
        dict: status and result or error msg.
    """

    try:
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
        report = (
            f"The current time in {city} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
        )
        return {"status": "success", "report": report}
    except Exception as e:
        return {
            "status": "error",
            "error_message": (
                str(e)
                # f"Sorry, I don't have timezone information for {city}."
            ),
        }


root_agent = Agent(
    name="weather_time_agent",
    model=LiteLlm(model="ollama_chat/mistral-small3.1"),
    description=("Agent to answer questions about the time and weather in a city."),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city."
    ),
    tools=[get_weather, get_current_time],
)
