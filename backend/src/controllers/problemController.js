import Problem, { CATEGORIES, STATUSES } from "../models/Problem.js";
import Comment from "../models/Comment.js";
import Solution from "../models/Solution.js";
import User from "../models/User.js";
import ApiError from "../utils/ApiError.js";
import { assertOwnerOrAdmin } from "../middleware/auth.js";
import { serializeProblem } from "../utils/serializers.js";
import { findSimilarProblems, problemText, refreshProblemSimilarity } from "../services/similarityService.js";
import {
    assertObjectId,
    escapeRegex,
    parsePagination,
    pickProblemFields,
    queryText,
    validateProblemText
} from "../utils/validators.js";

const SORT_OPTIONS={
    newest:{createdAt:-1},
    oldest:{createdAt:1},
    top:{upvoteCount:-1,createdAt:-1},
    discussed:{commentCount:-1,createdAt:-1},
    solutions:{solutionCount:-1,createdAt:-1}
};

async function findProblemOr404(id) {
    assertObjectId(id, "problem id");
    const problem=await Problem.findById(id);

    if (!problem) {
        throw new ApiError(404, "Problem not found");
    }

    return problem;
}

function buildListFilter(query) {
    const filter={};
    const search=queryText(query.q);
    const category=queryText(query.category);
    const status=queryText(query.status);
    const tag=queryText(query.tag).toLowerCase();
    const author=queryText(query.author);

    if (search) {
        const words=search.split(/\s+/).slice(0, 8);

        filter.$and=words.map((word) => {
            const pattern=new RegExp(escapeRegex(word), "i");
            return {$or:[{title:pattern},{description:pattern},{tags:pattern}]};
        });
    }

    if (category) filter.category=category;
    if (status) filter.status=status;
    if (tag) filter.tags=tag;

    if (author) {
        assertObjectId(author, "author id");
        filter.author=author;
    }

    return filter;
}

export async function listProblems(req, res) {
    const filter=buildListFilter(req.query);
    const sort=SORT_OPTIONS[queryText(req.query.sort)] || SORT_OPTIONS.newest;
    const {page, limit, skip}=parsePagination(req.query);

    const [problems, total]=await Promise.all([
        Problem.find(filter).sort(sort).skip(skip).limit(limit).populate("author", "name role"),
        Problem.countDocuments(filter)
    ]);

    res.json({
        problems:problems.map((problem) => serializeProblem(problem, req.user)),
        pagination:{page,limit,total,pages:Math.ceil(total / limit)}
    });
}

export function listOptions(req, res) {
    res.json({categories:CATEGORIES,statuses:STATUSES,sorts:Object.keys(SORT_OPTIONS)});
}

export async function getProblem(req, res) {
    assertObjectId(req.params.id, "problem id");

    const problem=await Problem.findById(req.params.id)
        .populate("author", "name role bio")
        .populate("similarAtSubmission.problem", "title status upvoteCount");

    if (!problem) {
        throw new ApiError(404, "Problem not found");
    }

    res.json({problem:serializeProblem(problem, req.user)});
}

export async function createProblem(req, res) {
    validateProblemText(req.body);

    const fields=pickProblemFields(req.body);
    delete fields.status;

    const problem=await Problem.create({...fields,author:req.user._id});
    const similarity=await refreshProblemSimilarity(problem, req.id);

    await problem.populate("author", "name role");

    res.status(201).json({
        problem:serializeProblem(problem, req.user),
        similarProblems:similarity.matches,
        aiAvailable:similarity.available
    });
}

export async function updateProblem(req, res) {
    const problem=await findProblemOr404(req.params.id);
    assertOwnerOrAdmin(problem.author, req.user);

    problem.set(pickProblemFields(req.body));

    const textChanged=problem.isModified("title") || problem.isModified("description");

    if (textChanged) {
        problem.embedding=undefined;
    }

    await problem.save();

    if (textChanged) {
        await refreshProblemSimilarity(problem, req.id);
    }

    await problem.populate("author", "name role");
    res.json({problem:serializeProblem(problem, req.user)});
}

export async function deleteProblem(req, res) {
    const problem=await findProblemOr404(req.params.id);
    assertOwnerOrAdmin(problem.author, req.user);

    await Promise.all([
        Comment.deleteMany({problem:problem._id}),
        Solution.deleteMany({problem:problem._id}),
        problem.deleteOne()
    ]);

    res.status(204).end();
}

export async function toggleUpvote(req, res) {
    assertObjectId(req.params.id, "problem id");
    const userId=req.user._id;

    let problem=await Problem.findOneAndUpdate(
        {_id:req.params.id,upvotes:{$ne:userId}},
        {$addToSet:{upvotes:userId},$inc:{upvoteCount:1}},
        {new:true}
    );
    let upvoted=true;

    if (!problem) {
        problem=await Problem.findOneAndUpdate(
            {_id:req.params.id,upvotes:userId},
            {$pull:{upvotes:userId},$inc:{upvoteCount:-1}},
            {new:true}
        );
        upvoted=false;
    }

    if (!problem) {
        throw new ApiError(404, "Problem not found");
    }

    res.json({upvoted,upvoteCount:problem.upvoteCount});
}

export async function getSimilarProblems(req, res) {
    assertObjectId(req.params.id, "problem id");
    const problem=await Problem.findById(req.params.id).select("title description +embedding");

    if (!problem) {
        throw new ApiError(404, "Problem not found");
    }

    const result=await findSimilarProblems({
        text:problemText(problem),
        embedding:problem.embedding,
        excludeId:problem._id,
        requestId:req.id
    });

    if (!problem.embedding?.length) {
        problem.embedding=result.queryEmbedding;
        problem.embeddingModel=result.model;
        await problem.save();
    }

    res.json({similarProblems:result.matches});
}

export async function getPlatformStats(req, res) {
    const [problems, solved, solutions, users, developers]=await Promise.all([
        Problem.countDocuments(),
        Problem.countDocuments({status:"solved"}),
        Solution.countDocuments(),
        User.countDocuments(),
        User.countDocuments({role:"developer"})
    ]);

    res.json({stats:{problems,solved,solutions,users,developers}});
}
