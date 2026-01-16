import mongoose from "mongoose";
import { successResponse, errorResponse } from "../utils/response.js";

export const checkHealth = async (req, res) => {
    try {
        const dbState = mongoose.connection.readyState;
        const dbStatus = {
            0: "disconnected",
            1: "connected",
            2: "connecting",
            3: "disconnecting",
        };

        const healthData = {
            server: "running",
            database: dbStatus[dbState] || "unknown",
            timestamp: new Date(),
        };

        return successResponse(res, healthData, "System is healthy");
    } catch (error) {
        return errorResponse(res, error, "Health check failed");
    }
};
