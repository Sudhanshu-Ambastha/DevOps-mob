import Problem from "../models/Problem.js";
import Solution from "../models/Solution.js";
import ApiError from "../utils/ApiError.js";
import { assertOwnerOrAdmin } from "../middleware/auth.js";
import { assertObjectId, pickSolutionFields } from "../utils/validators.js";

async function findSolutionOr404(id) {
    assertObjectId(id, "solution id");
    const solution=await Solution.findById(id);

    if (!solution) {
        throw new ApiError(404, "Solution not found");
    }

    return solution;
}

export async function listSolutions(req, res) {
    assertObjectId(req.params.problemId, "problem id");

    const solutions=await Solution.find({problem:req.params.problemId})
        .sort({isAccepted:-1,createdAt:-1})
        .populate("author", "name role skills");

    res.json({solutions});
}

export async function createSolution(req, res) {
    assertObjectId(req.params.problemId, "problem id");
    const problem=await Problem.findById(req.params.problemId);

    if (!problem) {
        throw new ApiError(404, "Problem not found");
    }

    if (await Solution.exists({problem:problem._id,author:req.user._id})) {
        throw new ApiError(409, "You have already published a solution for this problem. Edit it instead.");
    }

    const solution=await Solution.create({
        ...pickSolutionFields(req.body),
        problem:problem._id,
        author:req.user._id
    });

    problem.solutionCount+=1;

    if (problem.status === "open") {
        problem.status="in-progress";
    }

    await problem.save();
    await solution.populate("author", "name role skills");

    res.status(201).json({solution});
}

export async function updateSolution(req, res) {
    const solution=await findSolutionOr404(req.params.id);
    assertOwnerOrAdmin(solution.author, req.user);

    solution.set(pickSolutionFields(req.body));
    await solution.save();
    await solution.populate("author", "name role skills");

    res.json({solution});
}

export async function deleteSolution(req, res) {
    const solution=await findSolutionOr404(req.params.id);
    assertOwnerOrAdmin(solution.author, req.user);

    await solution.deleteOne();

    const problem=await Problem.findById(solution.problem);

    if (problem) {
        problem.solutionCount=Math.max(problem.solutionCount - 1, 0);

        if (solution.isAccepted) {
            problem.status=problem.solutionCount > 0 ? "in-progress" : "open";
        }

        await problem.save();
    }

    res.status(204).end();
}

export async function toggleAcceptSolution(req, res) {
    const solution=await findSolutionOr404(req.params.id);
    const problem=await Problem.findById(solution.problem);

    if (!problem) {
        throw new ApiError(404, "Problem not found");
    }

    if (String(problem.author) !== String(req.user._id) && req.user.role !== "admin") {
        throw new ApiError(403, "Only the problem author can accept a solution");
    }

    const accept=!solution.isAccepted;

    await Solution.updateMany({problem:problem._id}, {$set:{isAccepted:false}});

    solution.isAccepted=accept;
    problem.status=accept ? "solved" : "in-progress";

    await Promise.all([solution.save(), problem.save()]);
    await solution.populate("author", "name role skills");

    res.json({solution,problemStatus:problem.status});
}
