const startedAt=Date.now();

const counters={
    totalRequests:0,
    totalDurationMs:0,
    slowestMs:0,
    byStatusClass:{"2xx":0,"3xx":0,"4xx":0,"5xx":0}
};

export function recordRequest(statusCode, durationMs) {
    const statusClass=`${Math.floor(statusCode / 100)}xx`;

    counters.totalRequests+=1;
    counters.totalDurationMs+=durationMs;
    counters.slowestMs=Math.max(counters.slowestMs, durationMs);

    if (statusClass in counters.byStatusClass) {
        counters.byStatusClass[statusClass]+=1;
    }
}

export function getMetrics() {
    const average=counters.totalRequests ? counters.totalDurationMs / counters.totalRequests : 0;

    return {
        uptimeSeconds:Math.round((Date.now() - startedAt) / 1000),
        totalRequests:counters.totalRequests,
        averageResponseMs:Number(average.toFixed(2)),
        slowestResponseMs:Number(counters.slowestMs.toFixed(2)),
        responsesByStatus:{...counters.byStatusClass}
    };
}
