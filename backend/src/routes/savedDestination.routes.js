import express from "express";
import { authenticate } from "../middleware/auth.middleware.js";
import {
    saveDestination,
    getSavedDestinations,
    removeSavedDestination,
    checkIfSaved
} from "../controllers/savedDestination.controller.js";

const router = express.Router();

router.post("/", authenticate, saveDestination);
router.get("/", authenticate, getSavedDestinations);
router.get("/check/:destinationId", authenticate, checkIfSaved);
router.delete("/:id", authenticate, removeSavedDestination);

export default router;
