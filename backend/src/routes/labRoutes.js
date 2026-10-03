import express from "express";
import { requireAuth } from "../middleware/auth.js";
import { labLimiter } from "../middleware/rateLimiters.js";
import {
    cacheSimulation,
    cpuSimulation,
    memoryLocality,
    parallelBenchmark,
    systemInfo
} from "../controllers/labController.js";

const router=express.Router();

router.use(requireAuth);

router.get("/system", systemInfo);
router.post("/cache", cacheSimulation);
router.post("/cpu", cpuSimulation);
router.post("/memory", labLimiter, memoryLocality);
router.post("/parallel", labLimiter, parallelBenchmark);

export default router;
