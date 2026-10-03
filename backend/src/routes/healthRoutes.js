import express from "express";
import { health, healthDetails } from "../controllers/healthController.js";

const router=express.Router();

router.get("/", health);
router.get("/details", healthDetails);

export default router;
