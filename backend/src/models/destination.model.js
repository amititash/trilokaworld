import mongoose from "mongoose";

const destinationSchema = new mongoose.Schema({
    name: { type: String, required: true, unique: true },
    location: { type: String, required: true },
    description: { type: String, required: true },
    categories: { type: [String], required: true }, // Changed from category to categories
    rating: { type: Number, default: 4.5 },
    // price field removed
    emoji: { type: String, default: "🌍" },
    gradient: { type: String, default: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)" },
    badge: { type: String, default: "Popular" },
    images: { type: [String], default: [] },
    details: {
        history: { type: String },
        bestTime: { type: String },
        weather: { type: String },
        attractions: { type: String },
        forFamily: { type: String },
        forCouples: { type: String },
        forSolo: { type: String },
        forAdventure: { type: String },
        forVloggers: { type: String },
        culture: { type: String },
        food: { type: String },
        safety: { type: String },
        cost: { type: String },
        crowd: { type: String }
    }
}, { timestamps: true });

const Destination = mongoose.model("Destination", destinationSchema);

export default Destination;
