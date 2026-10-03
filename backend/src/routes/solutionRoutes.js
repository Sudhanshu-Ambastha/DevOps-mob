import express from "express";
import { requireAuth } from "../middleware/auth.js";
import { deleteSolution, toggleAcceptSolution, updateSolution } from "../controllers/solutionController.js";

const router=express.Router();

router.patch("/:id", requireAuth, updateSolution);
router.delete("/:id", requireAuth, deleteSolution);
router.patch("/:id/accept", requireAuth, toggleAcceptSolution);

export default router;
