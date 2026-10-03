import User from "../models/User.js";
import ApiError from "../utils/ApiError.js";
import { readToken, verifyToken } from "../utils/token.js";

async function findUserFromRequest(req) {
    const token=readToken(req);

    if (!token) {
        return null;
    }

    try {
        const payload=verifyToken(token);
        return await User.findById(payload.sub);
    } catch {
        return null;
    }
}

export async function requireAuth(req, res, next) {
    const user=await findUserFromRequest(req);

    if (!user) {
        throw new ApiError(401, "Please log in to continue");
    }

    req.user=user;
    next();
}

export async function optionalAuth(req, res, next) {
    req.user=await findUserFromRequest(req);
    next();
}

export function requireRole(...roles) {
    return (req, res, next) => {
        if (!req.user || !roles.includes(req.user.role)) {
            throw new ApiError(403, `This action requires one of these roles: ${roles.join(", ")}`);
        }

        next();
    };
}

export function assertOwnerOrAdmin(ownerId, user) {
    const isOwner=String(ownerId) === String(user._id);

    if (!isOwner && user.role !== "admin") {
        throw new ApiError(403, "You can only modify your own content");
    }
}
