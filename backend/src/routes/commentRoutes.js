import express from "express";
import { requireAuth } from "../middleware/auth.js";
import { deleteComment, updateComment } from "../controllers/commentController.js";

const router=express.Router();

router.patch("/:id", requireAuth, updateComment);
router.delete("/:id", requireAuth, deleteComment);

export default router;
