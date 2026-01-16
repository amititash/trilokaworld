import mongoose from "mongoose";

const tripSchema = new mongoose.Schema(
  {
    createdBy: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },

    tripName: { type: String, required: true },
    destination: { type: String, required: true },
    tripType: { type: String },

    startDate: { type: Date },
    endDate: { type: Date },
    days: Number,

    userInput: {
      numberOfPeople: Number,
      interests: [String],
      budget: String,
      pace: String,
      travelStyle: String,
      extraNotes: String
    },

    preferencesSnapshot: {
      travelerType: String,
      ageGroup: String,
      travelExperience: String,
      interests: [String],
      budget: String,
      crowd: String,
      pace: String,
      destinationType: [String]
    },

    itinerary: [
      {
        day: Number,
        title: String,
        description: String,
        activities: [String],
        travelTime: String,
        notes: String
      }
    ]
  },
  { timestamps: true }
);

export default mongoose.model("Trip", tripSchema);
