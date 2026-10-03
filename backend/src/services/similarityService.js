import Problem from "../models/Problem.js";
import env from "../config/env.js";
import logger from "../utils/logger.js";
import { aiClient } from "./aiClient.js";
import { summarizeProblem } from "../utils/serializers.js";

export function problemText(problem) {
    return `${problem.title}. ${problem.description}`;
}

async function saveComputedEmbeddings(computed, model) {
    const entries=Object.entries(computed || {});

    if (entries.length === 0) {
        return;
    }

    await Problem.bulkWrite(entries.map(([id, embedding]) => ({
        updateOne:{
            filter:{_id:id},
            update:{$set:{embedding,embeddingModel:model}}
        }
    })));

    logger.info("Stored embeddings computed by AI service", {count:entries.length});
}

export async function findSimilarProblems({text, embedding, excludeId, threshold=env.similarityThreshold, limit=5, semanticWeight=1, requestId}) {
    const filter=excludeId ? {_id:{$ne:excludeId}} : {};

    const candidates=await Problem.find(filter)
        .select("title description +embedding")
        .sort({createdAt:-1})
        .limit(env.maxSimilarityCandidates)
        .lean();

    const result=await aiClient.findSimilar({
        text,
        embedding:embedding?.length ? embedding : null,
        candidates:candidates.map((candidate) => ({
            id:String(candidate._id),
            text:problemText(candidate),
            embedding:candidate.embedding?.length ? candidate.embedding : null
        })),
        top_k:limit,
        threshold,
        semantic_weight:semanticWeight
    }, requestId);

    await saveComputedEmbeddings(result.computed_embeddings, result.model);

    const ids=result.matches.map((match) => match.id);
    const problems=await Problem.find({_id:{$in:ids}}).populate("author", "name role").lean();
    const problemsById=new Map(problems.map((problem) => [String(problem._id), problem]));

    const matches=result.matches
        .filter((match) => problemsById.has(match.id))
        .map((match) => ({
            problem:summarizeProblem(problemsById.get(match.id)),
            score:match.score,
            semanticScore:match.semantic_score,
            tfidfScore:match.tfidf_score
        }));

    return {matches,queryEmbedding:result.query_embedding,model:result.model};
}

export async function refreshProblemSimilarity(problem, requestId) {
    try {
        const result=await findSimilarProblems({text:problemText(problem),excludeId:problem._id,requestId});

        problem.embedding=result.queryEmbedding;
        problem.embeddingModel=result.model;
        problem.similarAtSubmission=result.matches.map((match) => ({problem:match.problem._id,score:match.score}));
        await problem.save();

        return {available:true,matches:result.matches};
    } catch (error) {
        logger.warn("Similarity analysis skipped", {problemId:String(problem._id),reason:error.message,requestId});
        return {available:false,matches:[]};
    }
}
