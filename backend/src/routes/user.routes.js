import express from "express";
import { authenticate } from "../middleware/auth.middleware.js";
import {
  createPreferences,
  updatePreferences,
  getPreferences
} from "../controllers/user.controller.js";

const router = express.Router();

router.post("/preferences", authenticate, createPreferences);
router.put("/preferences", authenticate, updatePreferences);
router.get("/preferences", authenticate, getPreferences);

export default router;
