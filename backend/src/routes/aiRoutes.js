import express from "express";
import { requireAuth } from "../middleware/auth.js";
import {
    aiStatus,
    analyzeText,
    checkDuplicates,
    compareTexts,
    semanticSearch,
    suggestMetadata
} from "../controllers/aiController.js";

const router=express.Router();

router.get("/status", aiStatus);
router.get("/search", semanticSearch);
router.post("/check-duplicates", requireAuth, checkDuplicates);
router.post("/suggest", requireAuth, suggestMetadata);
router.post("/analyze", analyzeText);
router.post("/compare", compareTexts);

export default router;
