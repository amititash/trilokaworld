import User from "../models/user.model.js";
import logger from "../utils/logger.js";
import { successResponse, errorResponse } from "../utils/response.js";

export const login = async (req, res) => {
  try {
    const { uid, email, name } = req.user;

    if (!uid) {
      logger.warn("Login Failed: Firebase UID missing from token");
      return errorResponse(res, null, "Firebase UID missing from token", 400);
    }

    logger.info(`Login attempt for UID: ${uid} | Email: ${email}`);

    // 1️⃣ Find by UID
    let user = await User.findOne({ uid });

    // 2️⃣ If not found by UID → Legacy migration by Email
    if (!user && email) {
      user = await User.findOne({ email });
      if (user) {
        logger.info(`Legacy migration: UID updated for email ${email}`);
        user.uid = uid;
        await user.save();
      }
    }

    // 3️⃣ Create new user if still not found
    if (!user) {
      user = await User.create({
        uid,
        email,
        name: name || "User",
        preferences: {},
      });
      logger.info(`New user created: ${uid}`);
    } else {
      logger.info(`User login success: ${uid}`);
    }

    // Check for preference availability
    const hasPreferences =
      user.preferences &&
      (
        user.preferences.travelerType ||
        user.preferences.budget ||
        (user.preferences.interests?.length > 0)
      );

    return successResponse(res, {
      user: {
        id: user._id,
        uid: user.uid,
        name: user.name,
        email: user.email,
      },
      hasPreferences: !!hasPreferences,
    }, "Login successful");

  } catch (error) {
    logger.error(`Login Error: ${error.message}`);
    return errorResponse(res, error, "Internal Server Error");
  }
};
