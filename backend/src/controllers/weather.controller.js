import axios from "axios";
import logger from "../utils/logger.js";
import { successResponse, errorResponse } from "../utils/response.js";

export const getWeather = async (req, res) => {
  try {
    const { lat, lon, city } = req.query;
    const apiKey = process.env.OPENWEATHER_API_KEY;

    if (!apiKey) {
      logger.error("OpenWeather API Key missing in environment variables");
      return errorResponse(res, null, "OpenWeather API key not configured", 500);
    }

    let url;
    if (lat && lon) {
      url = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&units=metric&appid=${apiKey}`;
      logger.info(`Fetching weather by coordinates: lat=${lat}, lon=${lon}`);
    } else if (city) {
      url = `https://api.openweathermap.org/data/2.5/weather?q=${city}&units=metric&appid=${apiKey}`;
      logger.info(`Fetching weather for city: ${city}`);
    } else {
      logger.warn("Weather request missing lat/lon or city");
      return errorResponse(res, null, "Latitude and Longitude or City is required", 400);
    }

    const response = await axios.get(url);
    const data = response.data;

    const weatherData = {
      temp: Math.round(data.main.temp),
      humidity: data.main.humidity,
      wind: Math.round(data.wind.speed * 3.6),
      description: data.weather[0].description,
      icon: data.weather[0].icon,
      city: data.name,
      country: data.sys.country,
    };

    logger.info(`Weather data served for: ${weatherData.city}, ${weatherData.country}`);

    successResponse(res, weatherData, "Weather data served");

  } catch (error) {
    logger.error(
      `Weather API Error: ${error.response?.data?.message || error.message}`
    );
    errorResponse(res, error, "Failed to fetch weather data");
  }
};
