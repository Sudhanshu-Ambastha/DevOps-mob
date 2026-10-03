import { after, before, describe, test } from "node:test";
import assert from "node:assert/strict";
import request from "supertest";
import { createUser, startTestApp } from "./setup.js";
import { simulateCache } from "../src/services/coa/cacheSimulator.js";
import { runProgram } from "../src/services/coa/cpuSimulator.js";

let context;
let member;

before(async () => {
    context=await startTestApp();
    member=await createUser(context.app);
});

after(async () => {
    await context.stop();
});

describe("Health and observability", () => {
    test("reports backend and database health", async () => {
        const response=await request(context.app).get("/api/health");

        assert.equal(response.status, 200);
        assert.equal(response.body.status, "ok");
        assert.equal(response.body.database, "connected");
        assert.ok(response.headers["x-request-id"]);
    });

    test("reports dependency details including a down AI service", async () => {
        const response=await request(context.app).get("/api/health/details");

        assert.equal(response.status, 200);
        assert.equal(response.body.dependencies.database.status, "connected");
        assert.equal(response.body.dependencies.aiService.status, "down");
        assert.ok(response.body.requests.totalRequests >= 1);
    });

    test("returns JSON 404 for unknown API routes", async () => {
        const response=await request(context.app).get("/api/does-not-exist");

        assert.equal(response.status, 404);
        assert.match(response.body.error.message, /Route not found/);
    });

    test("rejects malformed JSON bodies", async () => {
        const response=await request(context.app)
            .post("/api/auth/login")
            .set("Content-Type", "application/json")
            .send("{bad json");

        assert.equal(response.status, 400);
    });
});

describe("COA lab", () => {
    test("cache simulator gives 75% hits for sequential word access with 16-byte blocks", () => {
        const result=simulateCache({cacheSize:1024,blockSize:16,associativity:1,pattern:"sequential",accesses:2000,stride:4,arraySize:8192});

        assert.equal(result.hits + result.misses, 2000);
        assert.equal(result.hitRate, 0.75);
        assert.deepEqual(result.config.addressBits, {tag:22,index:6,offset:4});
    });

    test("a working set that fits in the cache only has compulsory misses", () => {
        const result=simulateCache({cacheSize:1024,blockSize:16,associativity:2,pattern:"sequential",accesses:4000,stride:4,arraySize:512});
        assert.equal(result.misses, 512 / 16);
    });

    test("toy CPU program computes the correct sum and CPI", () => {
        const result=runProgram({values:[3, 5, 7],memoryCycles:4});

        assert.equal(result.result, 15);
        assert.equal(result.verified, true);
        assert.equal(result.instructionCount, 3 + 3 * 6 + 2 + 2);
        assert.ok(result.cpi > 1);
    });

    test("lab endpoints require login", async () => {
        const response=await request(context.app).get("/api/lab/coa/system");
        assert.equal(response.status, 401);
    });

    test("runs the parallel similarity benchmark with matching results", async () => {
        const response=await member.agent.post("/api/lab/coa/parallel").send({vectorCount:2000,rounds:1,workers:2});

        assert.equal(response.status, 200);
        assert.equal(response.body.resultsMatch, true);
        assert.equal(response.body.workers, 2);
    });

    test("validates lab parameters", async () => {
        const response=await member.agent.post("/api/lab/coa/cache").send({cacheSize:1000});
        assert.equal(response.status, 400);
    });
});
