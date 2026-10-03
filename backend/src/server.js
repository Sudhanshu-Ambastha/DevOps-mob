import env from "./config/env.js";
import app from "./app.js";
import logger from "./utils/logger.js";
import { connectDatabase, disconnectDatabase } from "./config/db.js";

async function start() {
    await connectDatabase(env.mongoUri);

    const server=app.listen(env.port, () => {
        logger.info("Backend listening", {port:env.port,environment:env.nodeEnv,aiServiceUrl:env.aiServiceUrl});
    });

    async function shutdown(signal) {
        logger.info("Shutting down", {signal});

        server.close(async () => {
            await disconnectDatabase();
            process.exit(0);
        });

        setTimeout(() => process.exit(1), 10000).unref();
    }

    process.on("SIGTERM", () => shutdown("SIGTERM"));
    process.on("SIGINT", () => shutdown("SIGINT"));
}

start().catch((error) => {
    logger.error("Failed to start backend", {error:error.message});
    process.exit(1);
});
