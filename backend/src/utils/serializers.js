export function serializeProblem(problem, user) {
    const data=typeof problem.toObject === "function" ? problem.toObject() : {...problem};
    const upvotes=data.upvotes || [];

    data.hasUpvoted=user ? upvotes.some((id) => String(id) === String(user._id)) : false;
    data.similarAtSubmission=(data.similarAtSubmission || []).filter((item) => item.problem && item.problem.title);

    delete data.upvotes;
    delete data.embedding;
    delete data.embeddingModel;
    delete data.__v;

    return data;
}

export function summarizeProblem(problem) {
    const description=problem.description || "";

    return {
        _id:problem._id,
        title:problem.title,
        description:description.length > 220 ? `${description.slice(0, 220)}...` : description,
        category:problem.category,
        status:problem.status,
        tags:problem.tags,
        upvoteCount:problem.upvoteCount,
        commentCount:problem.commentCount,
        solutionCount:problem.solutionCount,
        author:problem.author,
        createdAt:problem.createdAt
    };
}
