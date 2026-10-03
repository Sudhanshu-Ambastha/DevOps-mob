import dotenv from "dotenv";

dotenv.config({path:[".env","../.env"],quiet:true});

const env={
    nodeEnv:process.env.NODE_ENV || "development",
    port:Number(process.env.PORT) || 5000,
    mongoUri:process.env.MONGO_URI || "mongodb://localhost:27017/devbridge",
    jwtSecret:process.env.JWT_SECRET,
    jwtExpiresIn:process.env.JWT_EXPIRES_IN || "7d",
    cookieSecure:process.env.COOKIE_SECURE === "true",
    bcryptRounds:Number(process.env.BCRYPT_ROUNDS) || 10,
    aiServiceUrl:process.env.AI_SERVICE_URL || "http://localhost:8000",
    aiTimeoutMs:Number(process.env.AI_TIMEOUT_MS) || 15000,
    similarityThreshold:Number(process.env.SIMILARITY_THRESHOLD) || 0.5,
    duplicateThreshold:Number(process.env.DUPLICATE_THRESHOLD) || 0.75,
    maxSimilarityCandidates:Number(process.env.MAX_SIMILARITY_CANDIDATES) || 500
};

if (!env.jwtSecret) {
    throw new Error("JWT_SECRET is not set. Copy .env.example to .env and set a long random value.");
}

export const isProduction=env.nodeEnv === "production";
export const isTest=env.nodeEnv === "test";

export default env;
