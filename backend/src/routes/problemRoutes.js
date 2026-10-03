import express from "express";
import { optionalAuth, requireAuth, requireRole } from "../middleware/auth.js";
import {
    createProblem,
    deleteProblem,
    getProblem,
    getSimilarProblems,
    listOptions,
    listProblems,
    toggleUpvote,
    updateProblem
} from "../controllers/problemController.js";
import { createComment, listComments } from "../controllers/commentController.js";
import { createSolution, listSolutions } from "../controllers/solutionController.js";

const router=express.Router();

router.get("/", optionalAuth, listProblems);
router.get("/options", listOptions);
router.post("/", requireAuth, createProblem);

router.get("/:id", optionalAuth, getProblem);
router.patch("/:id", requireAuth, updateProblem);
router.delete("/:id", requireAuth, deleteProblem);
router.post("/:id/upvote", requireAuth, toggleUpvote);
router.get("/:id/similar", getSimilarProblems);

router.get("/:problemId/comments", listComments);
router.post("/:problemId/comments", requireAuth, createComment);

router.get("/:problemId/solutions", listSolutions);
router.post("/:problemId/solutions", requireAuth, requireRole("developer", "admin"), createSolution);

export default router;
