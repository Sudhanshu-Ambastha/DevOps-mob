import mongoose from "mongoose";
import logger from "../utils/logger.js";

const stateNames={
    0:"disconnected",
    1:"connected",
    2:"connecting",
    3:"disconnecting"
};

export async function connectDatabase(uri) {
    mongoose.connection.on("disconnected", () => logger.warn("MongoDB disconnected"));
    mongoose.connection.on("reconnected", () => logger.info("MongoDB reconnected"));

    await mongoose.connect(uri, {serverSelectionTimeoutMS:10000});
    logger.info("MongoDB connected", {host:mongoose.connection.host,database:mongoose.connection.name});
}

export async function disconnectDatabase() {
    await mongoose.disconnect();
}

export function databaseState() {
    return stateNames[mongoose.connection.readyState] || "unknown";
}
