import { after, before, describe, test } from "node:test";
import assert from "node:assert/strict";
import request from "supertest";
import { createUser, sampleProblem, startTestApp } from "./setup.js";

let context;
let owner;
let stranger;

before(async () => {
    context=await startTestApp();
    owner=await createUser(context.app);
    stranger=await createUser(context.app);
});

after(async () => {
    await context.stop();
});

async function createProblem(agent, overrides={}) {
    const response=await agent.post("/api/problems").send({...sampleProblem,...overrides});
    assert.equal(response.status, 201, JSON.stringify(response.body));
    return response.body.problem;
}

describe("Problem CRUD", () => {
    test("requires authentication to create a problem", async () => {
        const response=await request(context.app).post("/api/problems").send(sampleProblem);
        assert.equal(response.status, 401);
    });

    test("validates the title and description", async () => {
        const response=await owner.agent.post("/api/problems").send({title:"Short",description:"Too short"});

        assert.equal(response.status, 400);
        assert.ok(response.body.error.details.title);
        assert.ok(response.body.error.details.description);
    });

    test("creates a problem even when the AI service is unavailable", async () => {
        const response=await owner.agent.post("/api/problems").send(sampleProblem);

        assert.equal(response.status, 201);
        assert.equal(response.body.problem.title, sampleProblem.title);
        assert.equal(response.body.problem.status, "open");
        assert.equal(response.body.problem.author.name, owner.user.name);
        assert.equal(response.body.aiAvailable, false);
        assert.equal(response.body.problem.embedding, undefined);
    });

    test("lists, searches and filters problems", async () => {
        await createProblem(owner.agent, {
            title:"Farmers do not know daily crop prices",
            description:"Small farmers sell crops at low prices because they cannot check market rates in nearby mandis.",
            category:"agriculture",
            tags:["farming","prices"]
        });

        const all=await request(context.app).get("/api/problems");
        assert.equal(all.status, 200);
        assert.ok(all.body.pagination.total >= 2);

        const search=await request(context.app).get("/api/problems").query({q:"crop prices"});
        assert.equal(search.body.problems.length, 1);
        assert.equal(search.body.problems[0].category, "agriculture");

        const byCategory=await request(context.app).get("/api/problems").query({category:"education"});
        assert.ok(byCategory.body.problems.every((problem) => problem.category === "education"));

        const byTag=await request(context.app).get("/api/problems").query({tag:"farming"});
        assert.equal(byTag.body.problems.length, 1);

        const byAuthor=await request(context.app).get("/api/problems").query({author:owner.user._id});
        assert.ok(byAuthor.body.problems.every((problem) => problem.author._id === owner.user._id));
    });

    test("gets a single problem and handles bad ids", async () => {
        const problem=await createProblem(owner.agent);

        const found=await request(context.app).get(`/api/problems/${problem._id}`);
        assert.equal(found.status, 200);
        assert.equal(found.body.problem._id, problem._id);

        const missing=await request(context.app).get("/api/problems/64b7f9f9f9f9f9f9f9f9f9f9");
        assert.equal(missing.status, 404);

        const invalid=await request(context.app).get("/api/problems/not-an-id");
        assert.equal(invalid.status, 400);
    });

    test("lets only the owner update a problem", async () => {
        const problem=await createProblem(owner.agent);

        const forbidden=await stranger.agent.patch(`/api/problems/${problem._id}`).send({title:"Hijacked title for this problem"});
        assert.equal(forbidden.status, 403);

        const updated=await owner.agent.patch(`/api/problems/${problem._id}`).send({status:"in-progress",tags:"Teams, College"});
        assert.equal(updated.status, 200);
        assert.equal(updated.body.problem.status, "in-progress");
        assert.deepEqual(updated.body.problem.tags, ["teams","college"]);

        const invalid=await owner.agent.patch(`/api/problems/${problem._id}`).send({status:"finished"});
        assert.equal(invalid.status, 400);
    });

    test("toggles upvotes once per user", async () => {
        const problem=await createProblem(owner.agent);

        const first=await stranger.agent.post(`/api/problems/${problem._id}/upvote`);
        assert.deepEqual(first.body, {upvoted:true,upvoteCount:1});

        const detail=await stranger.agent.get(`/api/problems/${problem._id}`);
        assert.equal(detail.body.problem.hasUpvoted, true);

        const second=await stranger.agent.post(`/api/problems/${problem._id}/upvote`);
        assert.deepEqual(second.body, {upvoted:false,upvoteCount:0});
    });

    test("lets only the owner delete a problem and removes its comments", async () => {
        const problem=await createProblem(owner.agent);
        await stranger.agent.post(`/api/problems/${problem._id}/comments`).send({body:"Same issue here"});

        const forbidden=await stranger.agent.delete(`/api/problems/${problem._id}`);
        assert.equal(forbidden.status, 403);

        const deleted=await owner.agent.delete(`/api/problems/${problem._id}`);
        assert.equal(deleted.status, 204);

        const {default:Comment}=await import("../src/models/Comment.js");
        assert.equal(await Comment.countDocuments({problem:problem._id}), 0);
        assert.equal((await request(context.app).get(`/api/problems/${problem._id}`)).status, 404);
    });

    test("returns 503 for AI features when the AI service is down", async () => {
        const response=await request(context.app).get("/api/ai/search").query({q:"find teammates"});
        assert.equal(response.status, 503);
    });
});
