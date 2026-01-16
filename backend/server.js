import dotenv from "dotenv";
dotenv.config();

const { default: app } = await import("./src/app.js");
import logger from "./src/utils/logger.js";

const PORT = process.env.PORT || 5000;

const server = app.listen(PORT, () => {
  logger.info(`Server is running on port ${PORT}`);
});

server.on("error", (err) => {
  if (err && err.code === "EADDRINUSE") {
    logger.error(`Port ${PORT} is already in use. Kill the process using it or change PORT in .env.`);
    process.exit(1);
  } else {
    logger.error(`Server error: ${err.message}`);
  }
});

const shutdown = () => {
  logger.info("Shutting down server...");
  server.close(() => process.exit(0));
};

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
