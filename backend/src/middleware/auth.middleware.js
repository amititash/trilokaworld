import admin from "../config/firebase.js";
import dotenv from "dotenv";
import User from "../models/user.model.js";
import logger from "../utils/logger.js";
import { errorResponse } from "../utils/response.js";

dotenv.config();

export const authenticate = async (req, res, next) => {
  const token = req.headers.authorization?.split(" ")[1];

  if (!token) {
    logger.warn("Unauthorized request — No token provided");
    return errorResponse(res, null, "No token provided", 401);
  }

  try {
    const decoded = await admin.auth().verifyIdToken(token);

    logger.info(`Token verified for UID: ${decoded.uid}`);

    const user = await User.findOne({ uid: decoded.uid });

    if (!user) {
      logger.warn(`User not found in DB for UID: ${decoded.uid} — Passing decoded token`);
      req.user = decoded; // Login endpoint will handle new user creation
    } else {
      logger.debug(`User ${user._id} attached to request`);
      req.user = user;
    }

    next();

  } catch (error) {
    logger.error(`Auth Error: ${error.message}`);
    return errorResponse(res, null, "Invalid Firebase token", 401);
  }
};
