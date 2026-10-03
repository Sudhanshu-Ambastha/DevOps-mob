import mongoose from "mongoose";
import ApiError from "./ApiError.js";

const EMAIL_PATTERN=/^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const SELF_ASSIGNABLE_ROLES=["user","developer"];

// ---------- Generic helpers ----------

export function cleanString(value) {
    return typeof value === "string" ? value.trim() : "";
}

export function checkLength(errors, field, value, label, min, max) {
    if (value.length < min) {
        errors[field]=`${label} must be at least ${min} characters`;
    } else if (value.length > max) {
        errors[field]=`${label} must be at most ${max} characters`;
    }
}

export function throwIfErrors(errors) {
    if (Object.keys(errors).length > 0) {
        throw new ApiError(400, "Validation failed", errors);
    }
}

export function assertObjectId(id, label="id") {
    if (!mongoose.isValidObjectId(id)) {
        throw new ApiError(400, `Invalid ${label}`);
    }
}

export function escapeRegex(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function queryText(value) {
    return typeof value === "string" ? value.trim() : "";
}

export function parsePagination(query, defaultLimit=12) {
    const page=Math.max(Number.parseInt(query.page) || 1, 1);
    const limit=Math.min(Math.max(Number.parseInt(query.limit) || defaultLimit, 1), 50);

    return {page,limit,skip:(page - 1) * limit};
}

export function normalizeList(value, maxItems, maxLength) {
    const items=Array.isArray(value) ? value : cleanString(value).split(",");

    const cleaned=items
        .filter((item) => typeof item === "string")
        .map((item) => item.trim().toLowerCase())
        .filter((item) => item.length > 0 && item.length <= maxLength);

    return [...new Set(cleaned)].slice(0, maxItems);
}

export function isValidUrl(value) {
    try {
        const url=new URL(value);
        return url.protocol === "http:" || url.protocol === "https:";
    } catch {
        return false;
    }
}

// ---------- Auth ----------

export function validateRegister(body={}) {
    const errors={};
    const name=cleanString(body.name);
    const email=cleanString(body.email).toLowerCase();
    const password=typeof body.password === "string" ? body.password : "";
    const role=body.role ? cleanString(body.role) : "user";

    checkLength(errors, "name", name, "Name", 2, 50);

    if (!EMAIL_PATTERN.test(email)) {
        errors.email="A valid email address is required";
    }

    if (password.length < 8) {
        errors.password="Password must be at least 8 characters";
    } else if (password.length > 72) {
        errors.password="Password must be at most 72 characters";
    }

    if (!SELF_ASSIGNABLE_ROLES.includes(role)) {
        errors.role="Role must be either user or developer";
    }

    throwIfErrors(errors);
    return {name,email,password,role};
}

export function validateLogin(body={}) {
    const email=cleanString(body.email).toLowerCase();
    const password=typeof body.password === "string" ? body.password : "";

    if (!email || !password) {
        throw new ApiError(400, "Email and password are required");
    }

    return {email,password};
}

// ---------- Profile ----------

export function validateProfileUpdate(body={}, currentRole) {
    const errors={};
    const update={};

    if (body.name !== undefined) {
        update.name=cleanString(body.name);
        checkLength(errors, "name", update.name, "Name", 2, 50);
    }

    if (body.bio !== undefined) {
        update.bio=cleanString(body.bio);
        checkLength(errors, "bio", update.bio, "Bio", 0, 300);
    }

    if (body.skills !== undefined) {
        update.skills=normalizeList(body.skills, 15, 30);
    }

    if (body.role !== undefined && currentRole !== "admin") {
        if (!SELF_ASSIGNABLE_ROLES.includes(body.role)) {
            errors.role="Role must be either user or developer";
        } else {
            update.role=body.role;
        }
    }

    throwIfErrors(errors);
    return update;
}

// ---------- Problems ----------

export function pickProblemFields(body={}) {
    const fields={};

    if (body.title !== undefined) fields.title=cleanString(body.title);
    if (body.description !== undefined) fields.description=cleanString(body.description);
    if (body.category !== undefined) fields.category=cleanString(body.category);
    if (body.status !== undefined) fields.status=cleanString(body.status);
    if (body.tags !== undefined) fields.tags=normalizeList(body.tags, 8, 30);

    return fields;
}

export function validateProblemText(body={}) {
    const errors={};
    const title=cleanString(body.title);
    const description=cleanString(body.description);

    checkLength(errors, "title", title, "Title", 10, 150);
    checkLength(errors, "description", description, "Description", 30, 5000);

    throwIfErrors(errors);
    return {title,description};
}

// ---------- Solutions ----------

export function pickSolutionFields(body={}) {
    const errors={};
    const fields={};

    if (body.title !== undefined) fields.title=cleanString(body.title);
    if (body.description !== undefined) fields.description=cleanString(body.description);
    if (body.techStack !== undefined) fields.techStack=normalizeList(body.techStack, 10, 30);

    for (const key of ["repoUrl","demoUrl"]) {
        if (body[key] === undefined) continue;

        const value=cleanString(body[key]);

        if (value && !isValidUrl(value)) {
            errors[key]="Must be a valid http(s) URL";
        }

        fields[key]=value;
    }

    throwIfErrors(errors);
    return fields;
}

// ---------- Comments ----------

export function validateCommentBody(body={}) {
    const errors={};
    const text=cleanString(body.body);

    checkLength(errors, "body", text, "Comment", 1, 1000);

    throwIfErrors(errors);
    return text;
}
