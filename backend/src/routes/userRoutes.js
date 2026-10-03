import express from "express";
import { requireAuth } from "../middleware/auth.js";
import { getMyDashboard, getUserProfile, updateMyProfile } from "../controllers/userController.js";

const router=express.Router();

router.get("/me/dashboard", requireAuth, getMyDashboard);
router.patch("/me", requireAuth, updateMyProfile);
router.get("/:id", getUserProfile);

export default router;
