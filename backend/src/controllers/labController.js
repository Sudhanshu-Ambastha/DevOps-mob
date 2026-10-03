import os from "node:os";
import Problem from "../models/Problem.js";
import ApiError from "../utils/ApiError.js";
import { PATTERNS, simulateCache } from "../services/coa/cacheSimulator.js";
import { measureMatrixTraversal } from "../services/coa/memoryLocality.js";
import { runProgram } from "../services/coa/cpuSimulator.js";
import { maxWorkers, runParallelBenchmark } from "../services/coa/parallelBenchmark.js";
import { createRandom } from "../services/coa/random.js";

const EMBEDDING_DIMENSIONS=384;

function integerInRange(value, label, min, max, fallback) {
    const number=value === undefined || value === "" ? fallback : Number(value);

    if (!Number.isInteger(number) || number < min || number > max) {
        throw new ApiError(400, `${label} must be a whole number between ${min} and ${max}`);
    }

    return number;
}

function powerOfTwo(value, label, min, max, fallback) {
    const number=integerInRange(value, label, min, max, fallback);

    if ((number & (number - 1)) !== 0) {
        throw new ApiError(400, `${label} must be a power of two`);
    }

    return number;
}

export function systemInfo(req, res) {
    const cpus=os.cpus();
    const memory=process.memoryUsage();
    const megabytes=(bytes) => Math.round(bytes / 1024 / 1024);

    res.json({
        cpu:{
            model:cpus[0]?.model || "unknown",
            logicalCores:cpus.length,
            availableParallelism:os.availableParallelism(),
            speedMhz:cpus[0]?.speed || null,
            architecture:os.arch(),
            endianness:os.endianness()
        },
        memory:{
            totalMb:megabytes(os.totalmem()),
            freeMb:megabytes(os.freemem()),
            processRssMb:megabytes(memory.rss),
            processHeapUsedMb:megabytes(memory.heapUsed)
        },
        platform:os.platform(),
        loadAverage:os.loadavg(),
        nodeVersion:process.version
    });
}

export function cacheSimulation(req, res) {
    const body=req.body || {};
    const pattern=body.pattern || "sequential";

    if (!PATTERNS.includes(pattern)) {
        throw new ApiError(400, `Pattern must be one of: ${PATTERNS.join(", ")}`);
    }

    const cacheSize=powerOfTwo(body.cacheSize, "Cache size", 64, 65536, 1024);
    const blockSize=powerOfTwo(body.blockSize, "Block size", 4, 256, 16);
    const associativity=powerOfTwo(body.associativity, "Associativity", 1, 16, 1);

    if (blockSize * associativity > cacheSize) {
        throw new ApiError(400, "Cache size must be at least block size x associativity");
    }

    const result=simulateCache({
        cacheSize,
        blockSize,
        associativity,
        pattern,
        accesses:integerInRange(body.accesses, "Accesses", 10, 100000, 2000),
        stride:integerInRange(body.stride, "Stride", 4, 4096, 64),
        arraySize:powerOfTwo(body.arraySize, "Array size", 64, 16777216, 8192),
        missPenalty:integerInRange(body.missPenalty, "Miss penalty", 1, 500, 100)
    });

    res.json(result);
}

export function memoryLocality(req, res) {
    const size=integerInRange(req.body?.size, "Matrix size", 64, 2048, 1024);
    res.json(measureMatrixTraversal(size));
}

export async function cpuSimulation(req, res) {
    const clockMhz=integerInRange(req.body?.clockMhz, "Clock speed", 1, 5000, 1000);
    const memoryCycles=integerInRange(req.body?.memoryCycles, "Memory cycles", 1, 200, 4);

    const problems=await Problem.find().select("upvoteCount").sort({createdAt:-1}).limit(200).lean();
    let values=problems.map((problem) => problem.upvoteCount);
    let source="database";

    if (values.length === 0) {
        const random=createRandom(3);
        values=Array.from({length:20}, () => Math.floor(random() * 50));
        source="generated";
    }

    res.json({source,...runProgram({values,clockMhz,memoryCycles})});
}

export async function parallelBenchmark(req, res) {
    const body=req.body || {};
    const limit=maxWorkers();

    const result=await runParallelBenchmark({
        vectorCount:integerInRange(body.vectorCount, "Vector count", 1000, 50000, 20000),
        dimensions:EMBEDDING_DIMENSIONS,
        rounds:integerInRange(body.rounds, "Rounds", 1, 20, 5),
        workers:integerInRange(body.workers, "Workers", 1, limit, Math.min(4, limit))
    });

    res.json(result);
}
