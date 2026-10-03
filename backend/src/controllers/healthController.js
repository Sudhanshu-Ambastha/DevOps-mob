import os from "node:os";
import pkg from "../../package.json" with { type:"json" };
import { databaseState } from "../config/db.js";
import { aiClient } from "../services/aiClient.js";
import { getMetrics } from "../utils/metrics.js";

export function health(req, res) {
    const database=databaseState();
    const healthy=database === "connected";

    res.status(healthy ? 200 : 503).json({
        status:healthy ? "ok" : "degraded",
        service:"backend",
        database,
        uptimeSeconds:Math.round(process.uptime()),
        timestamp:new Date().toISOString()
    });
}

export async function healthDetails(req, res) {
    const aiStart=Date.now();
    let ai;

    try {
        const response=await aiClient.health(req.id);
        ai={status:"up",latencyMs:Date.now() - aiStart,model:response.model,embeddingDimension:response.embedding_dimension};
    } catch {
        ai={status:"down",latencyMs:Date.now() - aiStart};
    }

    const memory=process.memoryUsage();
    const megabytes=(bytes) => Number((bytes / 1024 / 1024).toFixed(1));

    res.json({
        service:"backend",
        version:pkg.version,
        node:process.version,
        environment:process.env.NODE_ENV || "development",
        hostname:os.hostname(),
        dependencies:{
            database:{status:databaseState()},
            aiService:ai
        },
        memoryMb:{rss:megabytes(memory.rss),heapUsed:megabytes(memory.heapUsed),heapTotal:megabytes(memory.heapTotal)},
        requests:getMetrics()
    });
}
