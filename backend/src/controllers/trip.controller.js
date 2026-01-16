import Trip from "../models/trip.model.js";
import User from "../models/user.model.js";
import logger from "../utils/logger.js";
import { successResponse, errorResponse } from "../utils/response.js";

export const createTrip = async (req, res) => {
  try {
    const user = await User.findOne({ uid: req.user.uid });
    if (!user) {
      logger.warn(`CreateTrip: User not found - UID: ${req.user.uid}`);
      return errorResponse(res, null, "User not found", 404);
    }

    const trip = await Trip.create({
      createdBy: user._id,
      ...req.body
    });

    logger.info(`Trip created by ${user._id} | Trip ID: ${trip._id}`);
    successResponse(res, { trip }, "Trip created");

  } catch (error) {
    logger.error(`CreateTrip Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};

export const getTrips = async (req, res) => {
  try {
    const user = await User.findOne({ uid: req.user.uid });
    if (!user) {
      logger.warn(`GetTrips: User not found - UID: ${req.user.uid}`);
      return errorResponse(res, null, "User not found", 404);
    }

    const trips = await Trip.find({ createdBy: user._id });

    logger.info(`Trips fetched for user ${user._id}: ${trips.length} items`);
    successResponse(res, { trips }, "Trips fetched");

  } catch (error) {
    logger.error(`GetTrips Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};

export const getTripById = async (req, res) => {
  try {
    const user = await User.findOne({ uid: req.user.uid });
    if (!user) {
      logger.warn(`GetTripById: User not found - UID: ${req.user.uid}`);
      return errorResponse(res, null, "User not found", 404);
    }

    const trip = await Trip.findOne({
      _id: req.params.id,
      createdBy: user._id
    });

    if (!trip) {
      logger.warn(`Unauthorized or not found trip: ${req.params.id}`);
      return errorResponse(res, null, "Trip not found or unauthorized", 404);
    }

    logger.info(`Trip fetched: ${trip._id}`);
    successResponse(res, { trip }, "Trip fetched");

  } catch (error) {
    logger.error(`GetTripById Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};

export const updateTrip = async (req, res) => {
  try {
    const user = await User.findOne({ uid: req.user.uid });
    if (!user) {
      logger.warn(`UpdateTrip: User not found - UID: ${req.user.uid}`);
      return errorResponse(res, null, "User not found", 404);
    }

    const trip = await Trip.findOneAndUpdate(
      { _id: req.params.id, createdBy: user._id },
      req.body,
      { new: true }
    );

    if (!trip) {
      logger.warn(`Update failed (unauthorized or not found): ${req.params.id}`);
      return errorResponse(res, null, "Trip not found or unauthorized", 404);
    }

    logger.info(`Trip updated: ${trip._id}`);
    successResponse(res, { trip }, "Trip updated");

  } catch (error) {
    logger.error(`UpdateTrip Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};

export const deleteTrip = async (req, res) => {
  try {
    const user = await User.findOne({ uid: req.user.uid });
    if (!user) {
      logger.warn(`DeleteTrip: User not found - UID: ${req.user.uid}`);
      return errorResponse(res, null, "User not found", 404);
    }

    const trip = await Trip.findOneAndDelete({
      _id: req.params.id,
      createdBy: user._id
    });

    if (!trip) {
      logger.warn(`Delete failed (unauthorized or not found): ${req.params.id}`);
      return errorResponse(res, null, "Trip not found or unauthorized", 404);
    }

    logger.info(`Trip deleted: ${trip._id}`);
    successResponse(res, null, "Trip deleted");

  } catch (error) {
    logger.error(`DeleteTrip Error: ${error.message}`);
    errorResponse(res, error, "Server error");
  }
};
