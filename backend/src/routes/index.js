import express from "express";
import healthRoutes from "./healthRoutes.js";
import authRoutes from "./authRoutes.js";
import problemRoutes from "./problemRoutes.js";
import commentRoutes from "./commentRoutes.js";
import solutionRoutes from "./solutionRoutes.js";
import userRoutes from "./userRoutes.js";
import aiRoutes from "./aiRoutes.js";
import labRoutes from "./labRoutes.js";
import { getPlatformStats } from "../controllers/problemController.js";

const router=express.Router();

router.use("/health", healthRoutes);
router.use("/auth", authRoutes);
router.use("/problems", problemRoutes);
router.use("/comments", commentRoutes);
router.use("/solutions", solutionRoutes);
router.use("/users", userRoutes);
router.use("/ai", aiRoutes);
router.use("/lab/coa", labRoutes);
router.get("/stats", getPlatformStats);

export default router;
