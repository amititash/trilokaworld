import Destination from "../models/destination.model.js";
import axios from "axios";
import User from "../models/user.model.js";
import logger from "../utils/logger.js";
import { successResponse, errorResponse } from "../utils/response.js";

export const getAllDestinations = async (req, res) => {
  try {
    // Optimize: Select only necessary fields and limit images array
    const destinations = await Destination.find({}, {
      name: 1,
      location: 1,
      description: 1,
      categories: 1, // Required for filtering on frontend
      rating: 1,
      emoji: 1,
      gradient: 1,
      badge: 1,
      images: { $slice: 1 } // Only fetch 1 image for the list view to reduce payload
      // details is excluded
    });
    logger.info("Fetched all destinations (optimized view)");
    successResponse(res, destinations, "Fetched all destinations");
  } catch (error) {
    logger.error(`Get All Destinations Error: ${error.message}`);
    errorResponse(res, error);
  }
};

export const getDestinationById = async (req, res) => {
  try {
    const destination = await Destination.findById(req.params.id);
    if (!destination) {
      logger.warn(`Destination not found: ${req.params.id}`);
      return errorResponse(res, null, "Destination not found", 404);
    }

    logger.info(`Fetched destination by ID: ${req.params.id}`);
    successResponse(res, destination, "Fetched destination by ID");
  } catch (error) {
    logger.error(`Get Destination By ID Error: ${error.message}`);
    errorResponse(res, error);
  }
};

export const getRecommendations = async (req, res) => {
  try {
    let query = "popular tourist destinations";
    let p = null; // Preferences object source

    // 1️⃣ Priority: Check Request Body (From "AI Trip Planner" Modal)
    if (req.body.preferences && Object.keys(req.body.preferences).length > 0) {
      p = req.body.preferences;
      logger.info("Using Preferences from Request Body (Modal)");
    }
    // 2️⃣ Fallback: Check DB (Saved Profile)
    else if (req.user?.uid) {
      const user = await User.findOne({ uid: req.user.uid });
      if (user?.preferences) {
        p = user.preferences;
        logger.info("Using Preferences from Database (Saved Profile)");
      }
    }

    // 3️⃣ Construct Query String from 'p'
    if (p) {
      const parts = [];
      if (p.interests?.length > 0) parts.push(`best places for ${p.interests.join(", ")}`);
      if (p.destinationType?.length > 0) parts.push(`specifically ${p.destinationType.join(", ")}`);
      if (p.travelerType) parts.push(`suitable for ${p.travelerType} travelers`);
      if (p.ageGroup) parts.push(`in ${p.ageGroup} age group`);
      if (p.budget) parts.push(`with ${p.budget} budget`);
      if (p.pace) parts.push(`and ${p.pace} pace`);

      if (parts.length > 0) query = parts.join(" ");
    }

    logger.info(`Recommendation Query: "${query}"`);

    // 2️⃣ Call Search Service
    let baseUrl = process.env.SEARCH_SERVICE_URL || "http://smarrtour-search-service:8000";

    // Validate URL format (ensure http:// prefix)
    if (!baseUrl.startsWith("http")) {
      baseUrl = `http://${baseUrl}`;
    }

    try {
      new URL(baseUrl); // Validate URL syntax
    } catch (e) {
      logger.error(`Invalid SEARCH_SERVICE_URL: ${e.message}`);
      baseUrl = "http://search:8000";
    }

    const recommendUrl = `${baseUrl}/recommend`;
    logger.debug(`Calling AI Service → ${recommendUrl}`);

    try {
      let response;
      const maxRetries = 10;
      for (let i = 0; i < maxRetries; i++) {
        try {
          response = await axios.post(recommendUrl, {
            query,
            top_k: 3,
            interests: p ? [
              ...(p.interests || []),
              ...(p.destinationType || [])
            ] : []
          });
          break;
        } catch (err) {
          // Fail Fast if service is explicitly saying "I'm loading" (503)
          if (err.response && err.response.status === 503) {
            logger.warn("AI Service is loading (503). Skipping retries to fail fast.");
            throw err; // Break loop immediately
          }

          logger.warn(
            `AI Service Retry ${i + 1}/${maxRetries} failed: ${err.message}`
          );
          if (i === maxRetries - 1) throw err;
          await new Promise((r) => setTimeout(r, 3000));
        }
      }

      // Check for 'data' first (new format), fall back to 'success/recommendations' (old search service format)
      // The search service response might be { success: true, msg: "...", data: [...] } OR { success: true, recommendations: [...] }
      // We will handle this by checking response.data.data (if search svc is updated) or response.data.recommendations

      // NOTE: We are standardizing backend response, but search service might return nested data.
      // Assuming search service returns { data: [...] } or { recommendations: [...] } in its body.
      // Actually, axios wraps in data. So response.data is the body.

      const responseBody = response?.data || {};
      const destNames = responseBody.data || responseBody.recommendations || [];

      logger.info(`AI Recommended: ${JSON.stringify(destNames)}`);

      if (destNames.length > 0) {
        const destinations = await Destination.find({
          name: {
            $in: destNames.map((name) => new RegExp(`^${name}$`, "i")),
          },
        }, {
          name: 1, location: 1, description: 1, categories: 1, rating: 1, emoji: 1, gradient: 1, badge: 1, images: { $slice: 1 }
        });

        const sorted = destNames
          .map((name) =>
            destinations.find((d) => d.name.toLowerCase() === name.toLowerCase())
          )
          .filter(Boolean);

        if (sorted.length > 0) {
          logger.info("Recommendations served successfully");
          return successResponse(res, { recommendations: sorted }, "Recommendations served successfully");
        }
      }
    } catch (aiError) {
      logger.error(`AI Recommendation Failed. Using fallback: ${aiError.message}`);
    }

    // 3️⃣ Fallback random destinations
    const count = await Destination.countDocuments();
    const random = Math.floor(Math.random() * count);
    const fallback = await Destination.find({}, {
      name: 1, location: 1, description: 1, categories: 1, rating: 1, emoji: 1, gradient: 1, badge: 1, images: { $slice: 1 }
    })
      .limit(3)
      .skip(random % Math.max(1, count - 3));

    logger.info("Fallback random recommendations served");

    successResponse(res, { recommendations: fallback }, "Fallback random recommendations served");

  } catch (error) {
    logger.error(`Recommendation Controller Error: ${error.message}`);
    errorResponse(res, error);
  }
};
