import os from "node:os";
import { Worker } from "node:worker_threads";
import { buildDataset, scoreRange } from "./vectorMath.js";

const WORKER_FILE=new URL("./similarityWorker.js", import.meta.url);

function runWorker(workerData) {
    return new Promise((resolve, reject) => {
        const worker=new Worker(WORKER_FILE, {workerData});
        worker.once("message", resolve);
        worker.once("error", reject);
    });
}

function runSequential(vectors, query, dimensions, vectorCount, rounds) {
    const start=performance.now();
    let result;

    for (let round=0; round < rounds; round++) {
        result=scoreRange(vectors, query, dimensions, 0, vectorCount);
    }

    return {...result,ms:performance.now() - start};
}

async function runParallel(buffer, query, dimensions, vectorCount, rounds, workerCount) {
    const chunkSize=Math.ceil(vectorCount / workerCount);
    const start=performance.now();

    const jobs=Array.from({length:workerCount}, (_, index) => runWorker({
        buffer,
        query,
        dimensions,
        rounds,
        start:index * chunkSize,
        end:Math.min((index + 1) * chunkSize, vectorCount)
    }));

    const partials=await Promise.all(jobs);
    const best=partials.reduce((winner, partial) => partial.bestScore > winner.bestScore ? partial : winner);

    return {
        bestScore:best.bestScore,
        bestIndex:best.bestIndex,
        ms:performance.now() - start,
        slowestWorkerComputeMs:Math.max(...partials.map((partial) => partial.computeMs))
    };
}

export function maxWorkers() {
    return Math.min(os.availableParallelism(), 8);
}

export async function runParallelBenchmark({vectorCount, dimensions, rounds, workers}) {
    const {buffer, vectors, query}=buildDataset(vectorCount, dimensions);
    const sequential=runSequential(vectors, query, dimensions, vectorCount, rounds);
    const parallel=await runParallel(buffer, query, dimensions, vectorCount, rounds, workers);
    const speedup=sequential.ms / parallel.ms;
    const multiplyAdds=vectorCount * dimensions * 2 * rounds;

    return {
        workload:{vectorCount,dimensions,rounds,multiplyAdds,datasetMb:Number((buffer.byteLength / 1024 / 1024).toFixed(2))},
        cpuCores:os.availableParallelism(),
        workers,
        sequentialMs:Number(sequential.ms.toFixed(2)),
        parallelMs:Number(parallel.ms.toFixed(2)),
        slowestWorkerComputeMs:Number(parallel.slowestWorkerComputeMs.toFixed(2)),
        speedup:Number(speedup.toFixed(2)),
        efficiency:Number((speedup / workers).toFixed(2)),
        throughputMillionOpsPerSecond:Number((multiplyAdds / sequential.ms / 1000).toFixed(1)),
        resultsMatch:sequential.bestIndex === parallel.bestIndex,
        bestMatchIndex:sequential.bestIndex
    };
}
