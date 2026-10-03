import { createRandom } from "./random.js";

const WORD_SIZE=4;
const ADDRESS_BITS=32;

export const PATTERNS=["sequential","strided","random"];

function generateAddresses({pattern, accesses, stride, arraySize}) {
    const random=createRandom(7);
    const addresses=[];

    for (let i=0; i < accesses; i++) {
        if (pattern === "sequential") {
            addresses.push((i * WORD_SIZE) % arraySize);
        } else if (pattern === "strided") {
            addresses.push((i * stride) % arraySize);
        } else {
            addresses.push(Math.floor(random() * (arraySize / WORD_SIZE)) * WORD_SIZE);
        }
    }

    return addresses;
}

export function simulateCache(options) {
    const {cacheSize, blockSize, associativity, hitTime=1, missPenalty=100}=options;

    const totalLines=cacheSize / blockSize;
    const setCount=totalLines / associativity;
    const offsetBits=Math.log2(blockSize);
    const indexBits=Math.log2(setCount);

    const sets=Array.from({length:setCount}, () => []);
    const addresses=generateAddresses(options);
    const trace=[];

    let hits=0;
    let misses=0;
    let evictions=0;

    for (const address of addresses) {
        const block=Math.floor(address / blockSize);
        const setIndex=block % setCount;
        const tag=Math.floor(block / setCount);
        const set=sets[setIndex];
        const position=set.indexOf(tag);
        const isHit=position !== -1;

        if (isHit) {
            hits+=1;
            set.splice(position, 1);
        } else {
            misses+=1;

            if (set.length === associativity) {
                set.shift();
                evictions+=1;
            }
        }

        set.push(tag);

        if (trace.length < 16) {
            trace.push({address,block,set:setIndex,tag,result:isHit ? "hit" : "miss"});
        }
    }

    const hitRate=hits / addresses.length;
    const missRate=1 - hitRate;

    return {
        config:{
            cacheSize,
            blockSize,
            associativity,
            totalLines,
            sets:setCount,
            addressBits:{tag:ADDRESS_BITS - indexBits - offsetBits,index:indexBits,offset:offsetBits}
        },
        accesses:addresses.length,
        hits,
        misses,
        evictions,
        hitRate:Number(hitRate.toFixed(4)),
        missRate:Number(missRate.toFixed(4)),
        averageMemoryAccessTime:Number((hitTime + missRate * missPenalty).toFixed(2)),
        trace
    };
}
