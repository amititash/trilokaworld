import express from 'express';
import { getRecommendations } from '../controllers/recommendation.controller.js';
import { authenticate } from '../middleware/auth.middleware.js';

const router = express.Router();

// Protected route - user must be logged in to get personalized recommendations
router.post('/', authenticate, getRecommendations);

export default router;
