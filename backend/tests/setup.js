import request from "supertest";

export async function startTestApp({aiServiceUrl="http://127.0.0.1:9"}={}) {
    process.env.NODE_ENV="test";
    process.env.JWT_SECRET="test-only-secret";
    process.env.LOG_LEVEL="silent";
    process.env.BCRYPT_ROUNDS="4";
    process.env.AI_SERVICE_URL=aiServiceUrl;
    process.env.AI_TIMEOUT_MS="2000";

    const {MongoMemoryServer}=await import("mongodb-memory-server");
    const mongo=await MongoMemoryServer.create();

    const {connectDatabase, disconnectDatabase}=await import("../src/config/db.js");
    await connectDatabase(mongo.getUri());

    const {default:app}=await import("../src/app.js");

    return {
        app,
        async stop() {
            await disconnectDatabase();
            await mongo.stop();
        }
    };
}

let userCounter=0;

export async function createUser(app, overrides={}) {
    userCounter+=1;

    const agent=request.agent(app);
    const details={
        name:`Test User ${userCounter}`,
        email:`user${userCounter}@example.com`,
        password:"password123",
        role:"user",
        ...overrides
    };

    const response=await agent.post("/api/auth/register").send(details);

    if (response.status !== 201) {
        throw new Error(`Could not register test user: ${JSON.stringify(response.body)}`);
    }

    return {agent,user:response.body.user,details};
}

export const sampleProblem={
    title:"Students cannot find project teammates",
    description:"In my college, students struggle to find teammates with the right skills for semester projects and hackathons.",
    category:"education",
    tags:["college","teamwork"]
};
