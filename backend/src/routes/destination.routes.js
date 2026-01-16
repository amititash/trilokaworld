import express from "express";
import { getAllDestinations, getDestinationById, getRecommendations } from "../controllers/destination.controller.js";

import { authenticate } from "../middleware/auth.middleware.js";

const router = express.Router();

router.get("/recommendations", authenticate, getRecommendations);
router.get("/", getAllDestinations);
router.get("/:id", getDestinationById);

export default router;
