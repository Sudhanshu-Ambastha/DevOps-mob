import rateLimit from "express-rate-limit";
import { isTest } from "../config/env.js";

const limitMessage={error:{message:"Too many requests, please try again later"}};

export const authLimiter=rateLimit({
    windowMs:15 * 60 * 1000,
    limit:30,
    standardHeaders:"draft-7",
    legacyHeaders:false,
    message:limitMessage,
    skip:() => isTest
});

export const labLimiter=rateLimit({
    windowMs:60 * 1000,
    limit:20,
    standardHeaders:"draft-7",
    legacyHeaders:false,
    message:limitMessage,
    skip:() => isTest
});
