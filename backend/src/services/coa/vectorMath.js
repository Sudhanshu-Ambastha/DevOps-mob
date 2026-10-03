import { createRandom } from "./random.js";

export function buildDataset(vectorCount, dimensions, seed=11) {
    const random=createRandom(seed);
    const buffer=new SharedArrayBuffer(vectorCount * dimensions * Float32Array.BYTES_PER_ELEMENT);
    const vectors=new Float32Array(buffer);
    const query=new Float32Array(dimensions);

    for (let i=0; i < vectors.length; i++) {
        vectors[i]=random() * 2 - 1;
    }

    for (let i=0; i < dimensions; i++) {
        query[i]=random() * 2 - 1;
    }

    return {buffer,vectors,query};
}

export function scoreRange(vectors, query, dimensions, start, end) {
    let queryNorm=0;

    for (let d=0; d < dimensions; d++) {
        queryNorm+=query[d] * query[d];
    }

    queryNorm=Math.sqrt(queryNorm);

    let bestScore=-Infinity;
    let bestIndex=-1;

    for (let v=start; v < end; v++) {
        const offset=v * dimensions;
        let dot=0;
        let norm=0;

        for (let d=0; d < dimensions; d++) {
            const value=vectors[offset + d];
            dot+=value * query[d];
            norm+=value * value;
        }

        const score=dot / (Math.sqrt(norm) * queryNorm);

        if (score > bestScore) {
            bestScore=score;
            bestIndex=v;
        }
    }

    return {bestScore,bestIndex};
}
