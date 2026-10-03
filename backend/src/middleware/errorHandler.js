import logger from "../utils/logger.js";
import { isProduction } from "../config/env.js";

export function notFound(req, res) {
    res.status(404).json({error:{message:`Route not found: ${req.method} ${req.originalUrl}`}});
}

export function errorHandler(error, req, res, next) {
    let statusCode=error.statusCode || error.status || 500;
    let message=error.message || "Something went wrong";
    let details=error.details;

    if (error.name === "ValidationError") {
        statusCode=400;
        message="Validation failed";
        details=Object.fromEntries(Object.entries(error.errors).map(([field, fieldError]) => [field, fieldError.message]));
    } else if (error.name === "CastError") {
        statusCode=400;
        message=`Invalid value for ${error.path}`;
    } else if (error.code === 11000) {
        statusCode=409;
        message="A record with the same unique value already exists";
    } else if (error.type === "entity.parse.failed") {
        statusCode=400;
        message="Request body contains malformed JSON";
    }

    if (statusCode >= 500) {
        logger.error("Unhandled error", {requestId:req.id,path:req.originalUrl,error:error.message,stack:error.stack});

        if (isProduction) {
            message="Internal server error";
        }
    }

    if (res.headersSent) {
        return next(error);
    }

    res.status(statusCode).json({error:{message,details,requestId:req.id}});
}
