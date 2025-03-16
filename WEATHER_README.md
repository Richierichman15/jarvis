# Jarvis Weather Tool

This document explains how to set up and use the Weather feature in Jarvis.

## Overview

The Weather Tool allows Jarvis to fetch accurate weather information and forecasts for any location around the world. It uses the OpenWeatherMap API as its primary data source, with a fallback to web search if the API is unavailable or if the API key is not configured.

## Features

- **Current Weather**: Temperature, humidity, wind speed, and conditions
- **5-Day Forecast**: Daily forecasts showing expected conditions and temperature ranges
- **Timezone-Aware**: Shows sunrise and sunset times in local time
- **Multiple Location Support**: Works with city names, city+country combinations
- **Smart Caching**: Caches results for 30 minutes to avoid excessive API calls
- **Web Search Fallback**: Falls back to web search if API is unavailable

## Setup

### OpenWeatherMap API Key

To get the most accurate weather data, you'll need to obtain an API key from OpenWeatherMap:

1. Visit [OpenWeatherMap](https://openweathermap.org/) and sign up for a free account
2. Navigate to your API keys section
3. Create a new API key (or use the default one provided)
4. Set the API key in your environment:

```bash
export OPENWEATHER_API_KEY="your_api_key_here"
```

Or add it to your `.env` file:

```
OPENWEATHER_API_KEY=your_api_key_here
```

**Note**: Without an API key, the Weather Tool will still work, but it will use web search results which may be less accurate.

## Usage

### Using the CLI

Get weather information directly from the command line:

```bash
python main.py weather "New York"
python main.py weather "London, UK"
python main.py weather "Tokyo, Japan"
```

### In Chat

You can ask Jarvis about the weather naturally in a conversation:

```
You: What's the weather like in Paris?
You: Will it rain in Seattle this weekend?
You: How hot is it in Dubai right now?
You: What's the temperature in San Francisco?
```

## Implementation Details

The Weather Tool is implemented as part of the WebResearcher class in `jarvis/tools/web_researcher.py`. It works by:

1. Calling the OpenWeatherMap API to get current conditions
2. Fetching the 5-day forecast from the same API
3. Processing the forecast data to calculate daily averages and determine main conditions
4. Formatting the results in a readable way
5. Falling back to web search if the API call fails

## Troubleshooting

If you're having issues with the Weather Tool:

1. Check if your API key is correctly set in the environment
2. Ensure the location name is valid and spelled correctly
3. If using a city with a common name, try adding the country code (e.g., "Paris, FR")
4. Check your internet connection
5. Verify that OpenWeatherMap services are up and running

For API usage limits and other details, refer to the [OpenWeatherMap documentation](https://openweathermap.org/api). 