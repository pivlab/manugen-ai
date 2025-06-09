import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent

from google.adk.models.lite_llm import LiteLlm

def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }


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
            f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
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
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city."
    ),
    tools=[get_weather, get_current_time],
)
