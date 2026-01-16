import mongoose from "mongoose";

const savedDestinationSchema = new mongoose.Schema(
    {
        userId: {
            type: mongoose.Schema.Types.ObjectId,
            ref: "User",
            required: true
        },
        destinationId: {
            type: mongoose.Schema.Types.ObjectId,
            ref: "Destination",
            required: true
        },
        notes: {
            type: String
        },
    },
    { timestamps: true }
);

// Create compound index to prevent duplicate saves
savedDestinationSchema.index({ userId: 1, destinationId: 1 }, { unique: true });

export default mongoose.model("SavedDestination", savedDestinationSchema);
