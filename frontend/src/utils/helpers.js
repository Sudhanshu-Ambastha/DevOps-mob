export function createId() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

export function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString("en-IN", {day:"numeric",month:"short",year:"numeric"});
}

export function splitList(text) {
    return text
        .split(",")
        .map((item) => item.trim())
        .filter((item) => item !== "");
}

export function shortText(text, length) {
    return text.length > length ? text.slice(0, length) + "..." : text;
}

export function statusLabel(status) {
    if (status === "in-progress") return "In progress";
    if (status === "solved") return "Solved";
    return "Open";
}
