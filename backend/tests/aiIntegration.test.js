import { after, before, describe, test } from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import request from "supertest";
import { createUser, sampleProblem, startTestApp } from "./setup.js";

// Test double that follows the AI service contract (word-overlap instead of a transformer)
const receivedRequests=[];

function overlap(a, b) {
    const wordsA=new Set(a.toLowerCase().match(/[a-z]+/g));
    const wordsB=new Set(b.toLowerCase().match(/[a-z]+/g));
    const shared=[...wordsA].filter((word) => wordsB.has(word)).length;
    return shared / Math.max(new Set([...wordsA, ...wordsB]).size, 1);
}

function handleFindSimilar(body) {
    const computed={};

    for (const candidate of body.candidates) {
        if (!candidate.embedding) {
            computed[candidate.id]=[0.1, 0.2, 0.3];
        }
    }

    const matches=body.candidates
        .map((candidate) => {
            const score=overlap(body.text, candidate.text);
            return {id:candidate.id,score,semantic_score:score,tfidf_score:score};
        })
        .filter((match) => match.score >= body.threshold)
        .sort((a, b) => b.score - a.score)
        .slice(0, body.top_k);

    return {model:"stub-model",query_embedding:[0.3, 0.2, 0.1],matches,computed_embeddings:computed};
}

const stub=http.createServer((req, res) => {
    let raw="";
    req.on("data", (chunk) => raw+=chunk);
    req.on("end", () => {
        const body=raw ? JSON.parse(raw) : {};
        receivedRequests.push({path:req.url,body,requestId:req.headers["x-request-id"]});

        let payload={detail:"not found"};
        let status=404;

        if (req.url === "/health") {
            status=200;
            payload={status:"ok",model:"stub-model",embedding_dimension:3};
        } else if (req.url === "/find-similar") {
            status=200;
            payload=handleFindSimilar(body);
        }

        res.writeHead(status, {"Content-Type":"application/json"});
        res.end(JSON.stringify(payload));
    });
});

let context;
let member;

before(async () => {
    await new Promise((resolve) => stub.listen(0, "127.0.0.1", resolve));
    context=await startTestApp({aiServiceUrl:`http://127.0.0.1:${stub.address().port}`});
    member=await createUser(context.app);
});

after(async () => {
    await context.stop();
    stub.close();
});

describe("Backend to AI service integration", () => {
    let firstProblemId;

    test("stores the embedding returned for a new problem", async () => {
        const response=await member.agent.post("/api/problems").send(sampleProblem);

        assert.equal(response.status, 201);
        assert.equal(response.body.aiAvailable, true);
        firstProblemId=response.body.problem._id;

        const {default:Problem}=await import("../src/models/Problem.js");
        const stored=await Problem.findById(firstProblemId).select("+embedding +embeddingModel");
        assert.deepEqual([...stored.embedding], [0.3, 0.2, 0.1]);
        assert.equal(stored.embeddingModel, "stub-model");
    });

    test("finds and stores similar problems when a related problem is submitted", async () => {
        const response=await member.agent.post("/api/problems").send({
            ...sampleProblem,
            title:"Students cannot find teammates for college projects"
        });

        assert.equal(response.status, 201);
        assert.equal(response.body.similarProblems[0].problem._id, firstProblemId);
        assert.ok(response.body.similarProblems[0].semanticScore > 0.5);

        const detail=await request(context.app).get(`/api/problems/${response.body.problem._id}`);
        assert.equal(detail.body.problem.similarAtSubmission[0].problem._id, firstProblemId);

        const lastCall=receivedRequests.at(-1);
        assert.equal(lastCall.path, "/find-similar");
        assert.ok(lastCall.requestId, "request id should be forwarded to the AI service");
        assert.ok(lastCall.body.candidates.every((candidate) => candidate.id !== response.body.problem._id));
    });

    test("flags likely duplicates before submission", async () => {
        const response=await member.agent.post("/api/ai/check-duplicates").send(sampleProblem);

        assert.equal(response.status, 200);
        assert.equal(response.body.hasLikelyDuplicate, true);
        assert.equal(response.body.similarProblems[0].isLikelyDuplicate, true);
    });

    test("reports AI service status through the backend", async () => {
        const response=await request(context.app).get("/api/ai/status");

        assert.equal(response.body.available, true);
        assert.equal(response.body.model, "stub-model");
    });
});
