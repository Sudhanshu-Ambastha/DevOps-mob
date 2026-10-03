import { after, before, describe, test } from "node:test";
import assert from "node:assert/strict";
import request from "supertest";
import { createUser, startTestApp } from "./setup.js";

let context;

before(async () => {
    context=await startTestApp();
});

after(async () => {
    await context.stop();
});

describe("Authentication", () => {
    test("registers a user, sets an httpOnly cookie and hides the password", async () => {
        const response=await request(context.app).post("/api/auth/register").send({
            name:"Asha",
            email:"asha@example.com",
            password:"strongpass1",
            role:"developer"
        });

        assert.equal(response.status, 201);
        assert.equal(response.body.user.email, "asha@example.com");
        assert.equal(response.body.user.role, "developer");
        assert.equal(response.body.user.password, undefined);
        assert.match(response.headers["set-cookie"][0], /devbridge_token=.+HttpOnly/);
    });

    test("stores only a bcrypt hash of the password", async () => {
        const {default:User}=await import("../src/models/User.js");
        const user=await User.findOne({email:"asha@example.com"}).select("+password");

        assert.notEqual(user.password, "strongpass1");
        assert.match(user.password, /^\$2[aby]\$/);
    });

    test("rejects duplicate emails", async () => {
        const response=await request(context.app).post("/api/auth/register").send({
            name:"Asha Again",
            email:"ASHA@example.com",
            password:"strongpass1"
        });

        assert.equal(response.status, 409);
    });

    test("validates registration input", async () => {
        const response=await request(context.app).post("/api/auth/register").send({name:"A",email:"bad",password:"123"});

        assert.equal(response.status, 400);
        assert.ok(response.body.error.details.name);
        assert.ok(response.body.error.details.email);
        assert.ok(response.body.error.details.password);
    });

    test("does not allow self-registration as admin", async () => {
        const response=await request(context.app).post("/api/auth/register").send({
            name:"Sneaky",
            email:"sneaky@example.com",
            password:"strongpass1",
            role:"admin"
        });

        assert.equal(response.status, 400);
    });

    test("logs in with correct credentials and rejects wrong ones", async () => {
        const wrong=await request(context.app).post("/api/auth/login").send({email:"asha@example.com",password:"wrongpass1"});
        assert.equal(wrong.status, 401);

        const agent=request.agent(context.app);
        const login=await agent.post("/api/auth/login").send({email:"asha@example.com",password:"strongpass1"});
        assert.equal(login.status, 200);

        const me=await agent.get("/api/auth/me");
        assert.equal(me.status, 200);
        assert.equal(me.body.user.name, "Asha");
    });

    test("protects the current-user route and clears the session on logout", async () => {
        const anonymous=await request(context.app).get("/api/auth/me");
        assert.equal(anonymous.status, 401);

        const {agent}=await createUser(context.app);
        assert.equal((await agent.get("/api/auth/me")).status, 200);

        await agent.post("/api/auth/logout");
        assert.equal((await agent.get("/api/auth/me")).status, 401);
    });

    test("updates the user's own profile", async () => {
        const {agent}=await createUser(context.app);
        const response=await agent.patch("/api/users/me").send({bio:"I build tools",skills:"React, Node, react"});

        assert.equal(response.status, 200);
        assert.equal(response.body.user.bio, "I build tools");
        assert.deepEqual(response.body.user.skills, ["react","node"]);
    });
});
