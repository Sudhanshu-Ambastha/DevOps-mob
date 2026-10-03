import crypto from "node:crypto";
import logger from "../utils/logger.js";
import { recordRequest } from "../utils/metrics.js";

export default function requestLogger(req, res, next) {
    const start=process.hrtime.bigint();

    req.id=req.headers["x-request-id"] || crypto.randomUUID();
    res.setHeader("X-Request-Id", req.id);

    res.on("finish", () => {
        const durationMs=Number(process.hrtime.bigint() - start) / 1e6;
        const isHealthCheck=req.originalUrl.startsWith("/api/health");
        const level=res.statusCode >= 500 ? "error" : isHealthCheck ? "debug" : "info";

        recordRequest(res.statusCode, durationMs);

        logger[level]("request", {
            requestId:req.id,
            method:req.method,
            path:req.originalUrl,
            status:res.statusCode,
            durationMs:Number(durationMs.toFixed(2)),
            ip:req.ip,
            userId:req.user?._id ? String(req.user._id) : undefined
        });
    });

    next();
}
