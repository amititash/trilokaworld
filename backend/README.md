# SmartTour Backend

This is the Node.js/Express backend for the SmartTour application. It handles user authentication, data management (Trips, Destinations), and communicates with the MongoDB database.

## 📂 Folder Structure

- **`src/`**: Source code
  - **`config/`**: Database and Firebase configuration (`db.js`, `firebase.js`)
  - **`controllers/`**: Logic for handling requests (`auth.controller.js`, `trip.controller.js`, etc.)
  - **`middleware/`**: Express middleware (e.g., `auth.middleware.js` for verifying tokens)
  - **`models/`**: Mongoose schemas (`user.model.js`, `trip.model.js`)
  - **`routes/`**: API route definitions (`auth.routes.js`, `trip.routes.js`)
  - **`app.js`**: Main Express application setup
  - **`server.js`**: Entry point that starts the server
- **`seed_destinations.js`**: Script to populate the database with initial destination data.
- **`firebaseKey.json`**: (Required) Firebase Admin SDK credentials.

## 🚀 How to Run

### Prerequisites
- Node.js installed
- MongoDB running (locally or via Docker)
- `firebaseKey.json` placed in the root of this folder

### Local Development
1.  Install dependencies:
    ```bash
    npm install
    ```
2.  Start the server:
    ```bash
    npm run dev
    ```
    The server will start on `http://localhost:5000`.

### Docker
```bash
docker build -t smarttour-backend .
docker run -p 5000:5000 --env-file .env smarttour-backend
```

## 🔑 Key Environment Variables (`.env`)
- `MONGO_URI`: Connection string for MongoDB
- `PORT`: Port to run on (default 5000)
- `OPENWEATHER_API_KEY`: Key for fetching weather data
