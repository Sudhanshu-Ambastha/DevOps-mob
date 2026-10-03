import env from "../config/env.js";
import ApiError from "../utils/ApiError.js";
import logger from "../utils/logger.js";

async function callAiService(path, {body, requestId, timeoutMs=env.aiTimeoutMs}={}) {
    const start=Date.now();
    const headers={"Content-Type":"application/json"};

    if (requestId) {
        headers["X-Request-Id"]=requestId;
    }

    let response;

    try {
        response=await fetch(`${env.aiServiceUrl}${path}`, {
            method:body ? "POST" : "GET",
            headers,
            body:body ? JSON.stringify(body) : undefined,
            signal:AbortSignal.timeout(timeoutMs)
        });
    } catch (error) {
        logger.warn("AI service unreachable", {path,requestId,reason:error.message});
        throw new ApiError(503, "AI service is currently unavailable");
    }

    const data=await response.json().catch(() => ({}));

    logger.debug("AI service call", {path,status:response.status,durationMs:Date.now() - start,requestId});

    if (!response.ok) {
        logger.warn("AI service returned an error", {path,status:response.status,requestId});
        const statusCode=response.status === 422 ? 400 : 502;
        throw new ApiError(statusCode, "AI service could not process the request", data.detail);
    }

    return data;
}

export const aiClient={
    health:(requestId) => callAiService("/health", {requestId,timeoutMs:3000}),
    preprocess:(text, requestId) => callAiService("/nlp/preprocess", {body:{text},requestId}),
    keywords:(text, topK, requestId) => callAiService("/nlp/keywords", {body:{text,top_k:topK},requestId}),
    embed:(texts, requestId) => callAiService("/embeddings", {body:{texts},requestId}),
    compare:(textA, textB, requestId) => callAiService("/similarity", {body:{text_a:textA,text_b:textB},requestId}),
    classify:(text, labels, requestId) => callAiService("/classify", {body:{text,labels},requestId}),
    findSimilar:(payload, requestId) => callAiService("/find-similar", {body:payload,requestId})
};
