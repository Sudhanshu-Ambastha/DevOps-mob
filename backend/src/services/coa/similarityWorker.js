import { parentPort, workerData } from "node:worker_threads";
import { scoreRange } from "./vectorMath.js";

const {buffer, query, dimensions, start, end, rounds}=workerData;
const vectors=new Float32Array(buffer);
const begin=performance.now();

let result;

for (let round=0; round < rounds; round++) {
    result=scoreRange(vectors, query, dimensions, start, end);
}

parentPort.postMessage({...result,computeMs:performance.now() - begin});
