const INSTRUCTION_CLASS={
    LOADI:"alu",
    ADD:"alu",
    ADDI:"alu",
    CMP:"alu",
    LOAD:"memory",
    STORE:"memory",
    JMP:"branch",
    JGE:"branch",
    HALT:"control"
};

export function buildSumProgram(length) {
    return [
        {op:"LOADI",args:["R1", 0],note:"total = 0"},
        {op:"LOADI",args:["R2", 0],note:"i = 0"},
        {op:"LOADI",args:["R3", length],note:"n = number of problems"},
        {op:"CMP",args:["R2", "R3"],note:"compare i with n",label:"LOOP"},
        {op:"JGE",args:["END"],note:"exit loop when i >= n"},
        {op:"LOAD",args:["R4", "R2"],note:"R4 = upvotes[i]"},
        {op:"ADD",args:["R1", "R4"],note:"total += R4"},
        {op:"ADDI",args:["R2", 1],note:"i++"},
        {op:"JMP",args:["LOOP"],note:"repeat"},
        {op:"STORE",args:["R1", length],note:"memory[n] = total",label:"END"},
        {op:"HALT",args:[],note:"stop"}
    ];
}

export function formatInstruction(instruction) {
    return `${instruction.op} ${instruction.args.join(", ")}`.trim();
}

export function runProgram({values, clockMhz=1000, memoryCycles=4, branchCycles=2, traceLimit=30}) {
    const program=buildSumProgram(values.length);
    const memory=[...values, 0];
    const registers={R1:0,R2:0,R3:0,R4:0};
    const cyclesPerClass={alu:1,memory:memoryCycles,branch:branchCycles,control:1};
    const mix={alu:0,memory:0,branch:0,control:0};
    const labels=Object.fromEntries(program.flatMap((instruction, index) => instruction.label ? [[instruction.label, index]] : []));
    const trace=[];

    let pc=0;
    let cycles=0;
    let instructionCount=0;
    let greaterOrEqual=false;
    let running=true;

    while (running) {
        const instruction=program[pc];
        const [a, b]=instruction.args;
        const instructionClass=INSTRUCTION_CLASS[instruction.op];
        let nextPc=pc + 1;

        switch (instruction.op) {
            case "LOADI": registers[a]=b; break;
            case "ADD": registers[a]+=registers[b]; break;
            case "ADDI": registers[a]+=b; break;
            case "CMP": greaterOrEqual=registers[a] >= registers[b]; break;
            case "LOAD": registers[a]=memory[registers[b]]; break;
            case "STORE": memory[b]=registers[a]; break;
            case "JMP": nextPc=labels[a]; break;
            case "JGE": if (greaterOrEqual) nextPc=labels[a]; break;
            case "HALT": running=false; break;
        }

        instructionCount+=1;
        mix[instructionClass]+=1;
        cycles+=cyclesPerClass[instructionClass];

        if (trace.length < traceLimit) {
            trace.push({step:instructionCount,pc,instruction:formatInstruction(instruction),registers:{...registers},cycles});
        }

        pc=nextPc;
    }

    const result=memory[values.length];
    const expected=values.reduce((total, value) => total + value, 0);

    return {
        program:program.map((instruction, index) => ({address:index,label:instruction.label || "",code:formatInstruction(instruction),note:instruction.note})),
        inputSize:values.length,
        result,
        verified:result === expected,
        instructionCount,
        instructionMix:mix,
        cyclesPerClass,
        totalCycles:cycles,
        cpi:Number((cycles / instructionCount).toFixed(3)),
        clockMhz,
        cpuTimeMicroseconds:Number((cycles / clockMhz).toFixed(3)),
        trace
    };
}
