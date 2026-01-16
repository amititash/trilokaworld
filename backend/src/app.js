import express from "express";
import cors from "cors";
import { connectDB } from "./config/db.js";
import { authenticate } from "./middleware/auth.middleware.js";
import authRoutes from "./routes/auth.routes.js";
import userRoutes from "./routes/user.routes.js";
import tripRoutes from "./routes/trip.routes.js";
import destinationRoutes from "./routes/destination.routes.js";
import recommendationRoutes from "./routes/recommendation.routes.js";
import savedDestinationRoutes from "./routes/savedDestination.routes.js";
import weatherRoutes from "./routes/weather.routes.js";
import healthRoutes from "./routes/health.routes.js";
import logger from "./utils/logger.js";
import { successResponse, errorResponse } from "./utils/response.js";

const app = express();

// CORS Config
// app.use(cors({
//   origin: [
//     process.env.FRONTEND_URL || "http://localhost:5173",
//     "http://localhost:5174"
//   ],
//   credentials: true,
//   methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
//   allowedHeaders: ["Content-Type", "Authorization", "X-User-Email"]
// }));

// CORS Config
// app.use(cors({
//   origin: [
//     "*"
//   ],
//   // credentials: true,
//   // methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
//   // allowedHeaders: ["Content-Type", "Authorization", "X-User-Email"]
// }));

app.use(
	cors({
		origin: "*",
		methods: "*",
	})
);

app.use(express.json());

// Connect to MongoDB
connectDB();

// Root route
app.get("/", (req, res) => {
  logger.info("Backend root route accessed");
  successResponse(res, null, "Backend is running...");
});

// Public Routes
app.use("/auth", authRoutes);
app.use("/api/destinations", destinationRoutes);
app.use("/api/weather", weatherRoutes);
app.use("/api/health", healthRoutes);

// Auth Required Routes
app.use(authenticate);
logger.info("Authentication Middleware Applied");

// Protected Routes
app.use("/user", userRoutes);
app.use("/trip", tripRoutes);

logger.info("Registering recommendation routes");
app.use("/api/recommendations", recommendationRoutes);

app.use("/api/saved-destinations", savedDestinationRoutes);

// Global 404 fallback
app.use((req, res) => {
  logger.warn(`404 - Route Not Found: ${req.originalUrl}`);
  errorResponse(res, null, "Route Not Found", 404);
});

export default app;
