import axios from "axios";
import Destination from "../models/destination.model.js";
import logger from "../utils/logger.js";
import { successResponse, errorResponse } from "../utils/response.js";

export const getRecommendations = async (req, res) => {
  try {
    let { interests, budget, travelerType, duration, destinationType } = req.body;

    // Fetch stored preferences if not provided
    if ((!interests?.length) && !travelerType && req.user?.uid) {
      try {
        const User = (await import("../models/user.model.js")).default;
        const user = await User.findOne({ uid: req.user.uid });

        if (user?.preferences) {
          logger.info(`Using stored preferences for UID: ${req.user.uid}`);
          interests = interests?.length ? interests : user.preferences.interests;
          travelerType = travelerType || user.preferences.travelerType;
          budget = budget || user.preferences.budget;
          destinationType = destinationType?.length ? destinationType : user.preferences.destinationType;
        }
      } catch (userError) {
        logger.error(`Error fetching user preferences: ${userError.message}`);
      }
    }

    // Construct query string
    let query = `Best destinations`;
    if (travelerType) query += ` for a ${travelerType}`;
    if (destinationType?.length) query += ` preferring ${destinationType.join(", ")} destinations`;
    if (interests?.length) query += ` interested in ${interests.join(", ")}`;
    if (budget) query += ` with a ${budget} budget`;
    if (duration) query += ` for ${duration}`;

    logger.info(`Generated Query: "${query}"`);



    // Robust URL construction
    const searchUrlEnv = process.env.SEARCH_SERVICE_URL || "http://127.0.0.1:8000";
    let baseUrl;
    try {
      baseUrl = new URL(searchUrlEnv).origin;
    } catch (e) {
      logger.error(`Invalid SEARCH_SERVICE_URL: ${e.message}`);
      baseUrl = "http://search-service:8003"; // Default fallback
    }
    // Ensure we are hitting the /search endpoint (or /recommend if preferred, but existing code used search)
    // Note: Existing code posted query to this URL. The api.py has /search and /recommend.
    // /search returns raw chunks. /recommend returns unique destinations.
    // The previous code seemed to want raw chunks to process manually? 
    // Wait, the previous code handled "vectorResults".
    // Let's stick to /search as it was intended, but ensuring no trailing slash.
    const searchServiceEndpoint = `${baseUrl}/search`;

    logger.debug(`Calling Search Service at: ${searchServiceEndpoint}`);

    logger.debug(`Incoming Body: ${JSON.stringify(req.body)}`);
    logger.debug(`Interests to send: ${JSON.stringify(interests)}`);

    try {
      const response = await axios.post(searchServiceEndpoint, {
        query: query,
        top_k: 3,
        interests: interests || []
      });

      // Handle both raw format and potentially new standardized format from Search Service
      vectorResults = response.data.data ? response.data.data : (response.data.results || []);

      logger.info(`Vector Search Results Found: ${vectorResults.length}`);
    } catch (error) {
      logger.error(`Vector Search Error: ${error.message}`);

      if (error.response) {
        logger.error(`Error Response: ${JSON.stringify(error.response.data)}`);
      }

      return errorResponse(res, null, "Recommendation service unavailable", 503);
    }

    if (!vectorResults?.length) {
      logger.warn("No vector results returned, sending empty response");
      return successResponse(res, { recommendations: [] }, "No vector results returned");
    }

    // Fetching DB matches
    const recommendations = [];

    for (const result of vectorResults) {
      const destName = result.destination;
      logger.debug(`Processing destination: ${destName}`);

      try {
        const destination = await Destination.findOne({
          name: { $regex: new RegExp(`^${destName}$`, "i") },
        });

        if (destination) {
          logger.debug(`Matched in MongoDB: ${destination.name}`);
          recommendations.push({
            ...destination.toObject(),
            matchReason: result.text,
            matchScore: result.distance,
          });
        } else {
          logger.warn(`Not found in MongoDB: ${destName}`);
        }
      } catch (dbError) {
        logger.error(`DB Error while searching ${destName}: ${dbError.message}`);
      }
    }

    logger.info(`Recommendations sent: ${recommendations.length}`);
    return successResponse(res, { recommendations }, "Recommendations sent");

  } catch (error) {
    logger.error(`Get Recommendations Controller Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};
