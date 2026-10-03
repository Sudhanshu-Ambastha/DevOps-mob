import env from "../config/env.js";
import ApiError from "../utils/ApiError.js";
import { CATEGORIES } from "../models/Problem.js";
import { aiClient } from "../services/aiClient.js";
import { findSimilarProblems } from "../services/similarityService.js";
import { cleanString, queryText } from "../utils/validators.js";

function requireText(value, label, min, max) {
    const text=cleanString(value);

    if (text.length < min || text.length > max) {
        throw new ApiError(400, `${label} must be between ${min} and ${max} characters`);
    }

    return text;
}

function draftText(body={}) {
    const title=cleanString(body.title);
    const description=cleanString(body.description);
    return requireText(`${title}. ${description}`, "Title and description together", 20, 5200);
}

export async function aiStatus(req, res) {
    try {
        const health=await aiClient.health(req.id);
        res.json({available:true,...health});
    } catch {
        res.json({available:false,status:"unavailable"});
    }
}

export async function checkDuplicates(req, res) {
    const result=await findSimilarProblems({text:draftText(req.body),limit:5,requestId:req.id});

    const matches=result.matches.map((match) => ({
        ...match,
        isLikelyDuplicate:match.score >= env.duplicateThreshold
    }));

    res.json({
        similarProblems:matches,
        hasLikelyDuplicate:matches.some((match) => match.isLikelyDuplicate),
        thresholds:{similar:env.similarityThreshold,duplicate:env.duplicateThreshold}
    });
}

export async function suggestMetadata(req, res) {
    const text=draftText(req.body);
    const labels=CATEGORIES.filter((category) => category !== "other");

    const [classification, keywords]=await Promise.all([
        aiClient.classify(text, labels, req.id),
        aiClient.keywords(text, 6, req.id)
    ]);

    res.json({
        category:classification.label,
        categoryScores:classification.scores,
        tags:keywords.keywords.map((keyword) => keyword.term)
    });
}

export async function analyzeText(req, res) {
    const text=requireText(req.body.text, "Text", 1, 5000);
    res.json(await aiClient.preprocess(text, req.id));
}

export async function compareTexts(req, res) {
    const textA=requireText(req.body.textA, "First text", 3, 5000);
    const textB=requireText(req.body.textB, "Second text", 3, 5000);
    const result=await aiClient.compare(textA, textB, req.id);

    res.json({
        semanticScore:result.semantic_score,
        tfidfScore:result.tfidf_score,
        sharedTerms:result.shared_terms,
        model:result.model
    });
}

export async function semanticSearch(req, res) {
    const query=queryText(req.query.q);

    if (query.length < 3 || query.length > 300) {
        throw new ApiError(400, "Search query must be between 3 and 300 characters");
    }

    const result=await findSimilarProblems({
        text:query,
        threshold:0.2,
        limit:20,
        semanticWeight:0.7,
        requestId:req.id
    });

    res.json({results:result.matches});
}
