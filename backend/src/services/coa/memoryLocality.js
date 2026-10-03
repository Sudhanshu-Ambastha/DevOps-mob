function timeBestOf(runs, task) {
    let best=Infinity;
    let result=0;

    for (let run=0; run < runs; run++) {
        const start=performance.now();
        result=task();
        best=Math.min(best, performance.now() - start);
    }

    return {ms:Number(best.toFixed(3)),result};
}

export function measureMatrixTraversal(size) {
    const matrix=new Float64Array(size * size);

    for (let i=0; i < matrix.length; i++) {
        matrix[i]=i % 10;
    }

    const rowMajor=timeBestOf(3, () => {
        let sum=0;

        for (let row=0; row < size; row++) {
            for (let col=0; col < size; col++) {
                sum+=matrix[row * size + col];
            }
        }

        return sum;
    });

    const columnMajor=timeBestOf(3, () => {
        let sum=0;

        for (let col=0; col < size; col++) {
            for (let row=0; row < size; row++) {
                sum+=matrix[row * size + col];
            }
        }

        return sum;
    });

    return {
        size,
        elements:matrix.length,
        matrixMb:Number((matrix.byteLength / 1024 / 1024).toFixed(2)),
        rowMajorMs:rowMajor.ms,
        columnMajorMs:columnMajor.ms,
        slowdown:Number((columnMajor.ms / rowMajor.ms).toFixed(2)),
        resultsMatch:rowMajor.result === columnMajor.result
    };
}
