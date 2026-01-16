import mongoose from "mongoose";
import logger from "../utils/logger.js";

export const connectDB = async () => {
  const MAX_RETRIES = 10;
  const RETRY_DELAY = 5000; // 5 seconds

  for (let i = 0; i < MAX_RETRIES; i++) {
    try {
      const baseUri = process.env.MONGO_URI;

      if (!baseUri) {
        throw new Error("MONGO_URI environment variable is not defined");
      }

      await mongoose.connect(baseUri, {
        dbName: "ai_travel",
      });

      logger.info("MongoDB Connected Successfully! 🟢");

      // Create init collection if DB is fresh
      const db = mongoose.connection.db;
      const collections = await db.listCollections({ name: "trips" }).toArray();

      if (collections.length === 0) {
        await db.createCollection("init");
        logger.info("Initialized MongoDB database structure 📦");
      }
      return; // Connection successful, exit function

    } catch (error) {
      logger.error(`MongoDB Connection Attempt ${i + 1}/${MAX_RETRIES} Failed: ${error.message} ❌`);
      if (i === MAX_RETRIES - 1) {
        logger.error("Max retries reached. Exiting application.");
        process.exit(1);
      }
      logger.info(`Retrying in ${RETRY_DELAY / 1000} seconds...`);
      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
    }
  }
};
