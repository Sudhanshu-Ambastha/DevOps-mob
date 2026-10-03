const levels={
    debug:10,
    info:20,
    warn:30,
    error:40,
    silent:100
};

const minimumLevel=levels[process.env.LOG_LEVEL] || levels.info;

function write(level, message, meta={}) {
    if (levels[level] < minimumLevel) {
        return;
    }

    const entry={
        time:new Date().toISOString(),
        level,
        service:"backend",
        message,
        ...meta
    };

    const line=JSON.stringify(entry);

    if (level === "error" || level === "warn") {
        console.error(line);
    } else {
        console.log(line);
    }
}

const logger={
    debug:(message, meta) => write("debug", message, meta),
    info:(message, meta) => write("info", message, meta),
    warn:(message, meta) => write("warn", message, meta),
    error:(message, meta) => write("error", message, meta)
};

export default logger;
