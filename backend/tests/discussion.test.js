import { after, before, describe, test } from "node:test";
import assert from "node:assert/strict";
import request from "supertest";
import { createUser, sampleProblem, startTestApp } from "./setup.js";

let context;
let author;
let developer;
let otherDeveloper;
let problemId;

const sampleSolution={
    title:"TeamUp matching board",
    description:"A web app where students list skills and get matched with teammates using filters.",
    repoUrl:"https://github.com/example/teamup",
    techStack:["React","Node"]
};

before(async () => {
    context=await startTestApp();
    author=await createUser(context.app);
    developer=await createUser(context.app, {role:"developer"});
    otherDeveloper=await createUser(context.app, {role:"developer"});

    const response=await author.agent.post("/api/problems").send(sampleProblem);
    problemId=response.body.problem._id;
});

after(async () => {
    await context.stop();
});

describe("Comments", () => {
    let commentId;

    test("adds a comment and increments the counter", async () => {
        const response=await developer.agent.post(`/api/problems/${problemId}/comments`).send({body:"Do you need a mobile app?"});

        assert.equal(response.status, 201);
        assert.equal(response.body.comment.author.name, developer.user.name);
        commentId=response.body.comment._id;

        const problem=await request(context.app).get(`/api/problems/${problemId}`);
        assert.equal(problem.body.problem.commentCount, 1);
    });

    test("rejects empty comments", async () => {
        const response=await developer.agent.post(`/api/problems/${problemId}/comments`).send({body:"   "});
        assert.equal(response.status, 400);
    });

    test("lists comments publicly", async () => {
        const response=await request(context.app).get(`/api/problems/${problemId}/comments`);
        assert.equal(response.body.comments.length, 1);
    });

    test("lets only the comment author edit it", async () => {
        const forbidden=await author.agent.patch(`/api/comments/${commentId}`).send({body:"Changed"});
        assert.equal(forbidden.status, 403);

        const edited=await developer.agent.patch(`/api/comments/${commentId}`).send({body:"Do you need a web or mobile app?"});
        assert.equal(edited.status, 200);
        assert.equal(edited.body.comment.edited, true);
    });

    test("deletes a comment and decrements the counter", async () => {
        const response=await developer.agent.delete(`/api/comments/${commentId}`);
        assert.equal(response.status, 204);

        const problem=await request(context.app).get(`/api/problems/${problemId}`);
        assert.equal(problem.body.problem.commentCount, 0);
    });
});

describe("Solutions", () => {
    let solutionId;

    test("only developers can publish solutions", async () => {
        const response=await author.agent.post(`/api/problems/${problemId}/solutions`).send(sampleSolution);
        assert.equal(response.status, 403);
    });

    test("validates solution URLs", async () => {
        const response=await developer.agent.post(`/api/problems/${problemId}/solutions`).send({...sampleSolution,repoUrl:"javascript:alert(1)"});
        assert.equal(response.status, 400);
        assert.ok(response.body.error.details.repoUrl);
    });

    test("publishes a solution and moves the problem to in-progress", async () => {
        const response=await developer.agent.post(`/api/problems/${problemId}/solutions`).send(sampleSolution);

        assert.equal(response.status, 201);
        assert.deepEqual(response.body.solution.techStack, ["react","node"]);
        solutionId=response.body.solution._id;

        const problem=await request(context.app).get(`/api/problems/${problemId}`);
        assert.equal(problem.body.problem.solutionCount, 1);
        assert.equal(problem.body.problem.status, "in-progress");
    });

    test("allows only one solution per developer per problem", async () => {
        const response=await developer.agent.post(`/api/problems/${problemId}/solutions`).send(sampleSolution);
        assert.equal(response.status, 409);
    });

    test("lets only the solution author edit it", async () => {
        const forbidden=await otherDeveloper.agent.patch(`/api/solutions/${solutionId}`).send({title:"Stolen solution"});
        assert.equal(forbidden.status, 403);

        const updated=await developer.agent.patch(`/api/solutions/${solutionId}`).send({demoUrl:"https://teamup.example.com"});
        assert.equal(updated.status, 200);
        assert.equal(updated.body.solution.demoUrl, "https://teamup.example.com");
    });

    test("lets the problem author accept a solution", async () => {
        const forbidden=await otherDeveloper.agent.patch(`/api/solutions/${solutionId}/accept`);
        assert.equal(forbidden.status, 403);

        const accepted=await author.agent.patch(`/api/solutions/${solutionId}/accept`);
        assert.equal(accepted.status, 200);
        assert.equal(accepted.body.solution.isAccepted, true);
        assert.equal(accepted.body.problemStatus, "solved");
    });

    test("shows contribution stats on the dashboard", async () => {
        const response=await developer.agent.get("/api/users/me/dashboard");

        assert.equal(response.status, 200);
        assert.equal(response.body.stats.solutions, 1);
        assert.equal(response.body.stats.acceptedSolutions, 1);
    });

    test("deletes a solution and updates the problem", async () => {
        const response=await developer.agent.delete(`/api/solutions/${solutionId}`);
        assert.equal(response.status, 204);

        const problem=await request(context.app).get(`/api/problems/${problemId}`);
        assert.equal(problem.body.problem.solutionCount, 0);
        assert.equal(problem.body.problem.status, "open");
    });
});
