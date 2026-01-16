import User from "../models/user.model.js";
import logger from "../utils/logger.js";
import { successResponse, errorResponse } from "../utils/response.js";

export const createPreferences = async (req, res) => {
  try {
    const user = await User.findOne({ uid: req.user.uid });

    if (!user) {
      logger.warn(`CreatePreferences: User not found - UID: ${req.user.uid}`);
      return errorResponse(res, null, "User not found", 404);
    }

    user.preferences = req.body;
    await user.save();

    logger.info(`Preferences created for user: ${user._id}`);
    successResponse(res, { preferences: user.preferences }, "Preferences created");

  } catch (error) {
    logger.error(`CreatePreferences Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};

export const updatePreferences = async (req, res) => {
  try {
    const user = await User.findOne({ uid: req.user.uid });

    if (!user) {
      logger.warn(`UpdatePreferences: User not found - UID: ${req.user.uid}`);
      return errorResponse(res, null, "User not found", 404);
    }

    user.preferences = req.body;
    await user.save();

    logger.info(`Preferences updated for user: ${user._id}`);
    successResponse(res, { preferences: user.preferences }, "Preferences updated");

  } catch (error) {
    logger.error(`UpdatePreferences Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};

export const getPreferences = async (req, res) => {
  try {
    const user = await User.findOne({ uid: req.user.uid });

    if (!user) {
      logger.warn(`GetPreferences: User not found, returning empty`);
      return successResponse(res, { preferences: {} }, "User not found, returning empty");
    }

    logger.info(`Fetched preferences for user: ${user._id}`);
    successResponse(res, { preferences: user.preferences || {} }, "Fetched preferences");

  } catch (error) {
    logger.error(`GetPreferences Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};
