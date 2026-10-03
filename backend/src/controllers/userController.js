import User from "../models/User.js";
import Problem from "../models/Problem.js";
import Solution from "../models/Solution.js";
import ApiError from "../utils/ApiError.js";
import { assertObjectId, validateProfileUpdate } from "../utils/validators.js";

async function contributionStats(userId) {
    const [problemCount, solutionCount, acceptedSolutions, upvoteTotals]=await Promise.all([
        Problem.countDocuments({author:userId}),
        Solution.countDocuments({author:userId}),
        Solution.countDocuments({author:userId,isAccepted:true}),
        Problem.aggregate([
            {$match:{author:userId}},
            {$group:{_id:null,total:{$sum:"$upvoteCount"}}}
        ])
    ]);

    return {
        problems:problemCount,
        solutions:solutionCount,
        acceptedSolutions,
        upvotesReceived:upvoteTotals[0]?.total || 0
    };
}

function recentSolutionsBy(userId, limit) {
    return Solution.find({author:userId})
        .sort({createdAt:-1})
        .limit(limit)
        .populate("problem", "title status");
}

export async function getUserProfile(req, res) {
    assertObjectId(req.params.id, "user id");
    const user=await User.findById(req.params.id);

    if (!user) {
        throw new ApiError(404, "User not found");
    }

    const [stats, problems, solutions]=await Promise.all([
        contributionStats(user._id),
        Problem.find({author:user._id}).sort({createdAt:-1}).limit(10).select("-upvotes"),
        recentSolutionsBy(user._id, 10)
    ]);

    res.json({
        user:{_id:user._id,name:user.name,role:user.role,bio:user.bio,skills:user.skills,createdAt:user.createdAt},
        stats,
        problems,
        solutions
    });
}

export async function updateMyProfile(req, res) {
    const update=validateProfileUpdate(req.body, req.user.role);

    req.user.set(update);
    await req.user.save();

    res.json({user:req.user});
}

export async function getMyDashboard(req, res) {
    const userId=req.user._id;
    const isDeveloper=["developer","admin"].includes(req.user.role);

    const [stats, recentProblems, recentSolutions]=await Promise.all([
        contributionStats(userId),
        Problem.find({author:userId}).sort({createdAt:-1}).limit(5).select("-upvotes"),
        recentSolutionsBy(userId, 5)
    ]);

    let suggestedProblems=[];

    if (isDeveloper) {
        const solvedByMe=await Solution.find({author:userId}).distinct("problem");

        suggestedProblems=await Problem.find({
            status:{$ne:"solved"},
            author:{$ne:userId},
            _id:{$nin:solvedByMe}
        })
            .sort({upvoteCount:-1,createdAt:-1})
            .limit(5)
            .select("-upvotes")
            .populate("author", "name");
    }

    res.json({stats,recentProblems,recentSolutions,suggestedProblems});
}
