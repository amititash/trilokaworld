import mongoose from "mongoose";

const userSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  uid: { type: String, required: true, unique: true },
  preferences: {
    travelerType: { type: String, default: null },
    ageGroup: { type: String, default: null },
    travelExperience: { type: String, default: null },

    interests: { type: [String], default: [] },

    budget: { type: String, default: null },
    crowd: { type: String, default: null },
    pace: { type: String, default: null },

    destinationType: { type: [String], default: [] }
  }
}, { timestamps: true });

const User = mongoose.models.User || mongoose.model("User", userSchema);

export default User;
