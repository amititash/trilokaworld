import SavedDestination from "../models/SavedDestination.model.js";
import Destination from "../models/destination.model.js";
import logger from "../utils/logger.js";
import { successResponse, errorResponse } from "../utils/response.js";

// Save a destination
export const saveDestination = async (req, res) => {
  try {
    const { destinationId, notes } = req.body;
    const userId = req.user._id;

    logger.info(`User ${userId} trying to save destination ${destinationId}`);

    const destination = await Destination.findById(destinationId);
    if (!destination) {
      logger.warn(`Destination not found: ${destinationId}`);
      return errorResponse(res, null, "Destination not found", 404);
    }

    const existingSave = await SavedDestination.findOne({ userId, destinationId });
    if (existingSave) {
      logger.warn(`Destination already saved by ${userId}: ${destinationId}`);
      return errorResponse(res, null, "Destination already saved", 400);
    }

    const savedDestination = await SavedDestination.create({
      userId,
      destinationId,
      notes,
    });

    await savedDestination.populate("destinationId");

    logger.info(`Destination saved successfully for ${userId}: ${destinationId}`);
    successResponse(res, { savedDestination }, "Destination saved successfully", 201);
  } catch (error) {
    logger.error(`Save Destination Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};

// Get all saved destinations
export const getSavedDestinations = async (req, res) => {
  try {
    const userId = req.user._id;

    logger.info(`Fetching saved destinations for ${userId}`);

    const savedDestinations = await SavedDestination.find({ userId })
      .populate({
        path: "destinationId",
        select: { name: 1, location: 1, description: 1, rating: 1, emoji: 1, gradient: 1, badge: 1, images: { $slice: 1 } },
        match: { _id: { $exists: true } }
      })
      .sort({ createdAt: -1 });

    logger.info(`Results fetched: ${savedDestinations.length} items`);
    successResponse(res, {
      count: savedDestinations.length,
      savedDestinations,
    }, "Results fetched");
  } catch (error) {
    logger.error(`Get Saved Destinations Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};

// Remove a saved destination
export const removeSavedDestination = async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user._id;

    logger.warn(`User ${userId} trying to remove saved destination ${id}`);

    const savedDestination = await SavedDestination.findOneAndDelete({
      _id: id,
      userId,
    });

    if (!savedDestination) {
      logger.warn(`Saved destination not found for ${userId}: ${id}`);
      return errorResponse(res, null, "Saved destination not found", 404);
    }

    logger.info(`Saved destination removed: ${id} by ${userId}`);
    successResponse(res, { savedDestination }, "Destination removed from saved");
  } catch (error) {
    logger.error(`Remove Saved Destination Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};

// Check if destination is saved
export const checkIfSaved = async (req, res) => {
  try {
    const { destinationId } = req.params;
    const userId = req.user._id;

    logger.debug(`Checking saved status of ${destinationId} for user ${userId}`);

    const isSaved = await SavedDestination.exists({ userId, destinationId });

    logger.info(`Saved status for ${destinationId}: ${!!isSaved}`);
    successResponse(res, { isSaved: !!isSaved }, "Saved status");
  } catch (error) {
    logger.error(`Check Saved Status Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};
