import express from "express";
import { authenticate } from "../middleware/auth.middleware.js";
import {
  createTrip,
  getTrips,
  getTripById,
  updateTrip,
  deleteTrip
} from "../controllers/trip.controller.js";

const router = express.Router();

router.post("/", authenticate, createTrip);
router.get("/", authenticate, getTrips);
router.get("/:id", authenticate, getTripById);
router.put("/:id", authenticate, updateTrip);
router.delete("/:id", authenticate, deleteTrip);

export default router;
