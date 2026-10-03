import Comment from "../models/Comment.js";
import Problem from "../models/Problem.js";
import ApiError from "../utils/ApiError.js";
import { assertOwnerOrAdmin } from "../middleware/auth.js";
import { assertObjectId, validateCommentBody } from "../utils/validators.js";

async function findCommentOr404(id) {
    assertObjectId(id, "comment id");
    const comment=await Comment.findById(id);

    if (!comment) {
        throw new ApiError(404, "Comment not found");
    }

    return comment;
}

export async function listComments(req, res) {
    assertObjectId(req.params.problemId, "problem id");

    const comments=await Comment.find({problem:req.params.problemId})
        .sort({createdAt:1})
        .populate("author", "name role");

    res.json({comments});
}

export async function createComment(req, res) {
    assertObjectId(req.params.problemId, "problem id");
    const body=validateCommentBody(req.body);

    const problem=await Problem.findByIdAndUpdate(req.params.problemId, {$inc:{commentCount:1}});

    if (!problem) {
        throw new ApiError(404, "Problem not found");
    }

    const comment=await Comment.create({problem:problem._id,author:req.user._id,body});
    await comment.populate("author", "name role");

    res.status(201).json({comment});
}

export async function updateComment(req, res) {
    const comment=await findCommentOr404(req.params.id);

    if (String(comment.author) !== String(req.user._id)) {
        throw new ApiError(403, "You can only edit your own comments");
    }

    comment.body=validateCommentBody(req.body);
    comment.edited=true;
    await comment.save();
    await comment.populate("author", "name role");

    res.json({comment});
}

export async function deleteComment(req, res) {
    const comment=await findCommentOr404(req.params.id);
    assertOwnerOrAdmin(comment.author, req.user);

    await comment.deleteOne();
    await Problem.updateOne({_id:comment.problem}, {$inc:{commentCount:-1}});

    res.status(204).end();
}
