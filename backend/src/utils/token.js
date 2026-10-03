import jwt from "jsonwebtoken";
import env from "../config/env.js";

export const AUTH_COOKIE="devbridge_token";

const cookieOptions={
    httpOnly:true,
    sameSite:"lax",
    secure:env.cookieSecure,
    path:"/"
};

export function signToken(userId) {
    return jwt.sign({sub:String(userId)}, env.jwtSecret, {expiresIn:env.jwtExpiresIn});
}

export function verifyToken(token) {
    return jwt.verify(token, env.jwtSecret);
}

export function setAuthCookie(res, token) {
    res.cookie(AUTH_COOKIE, token, {...cookieOptions,maxAge:7 * 24 * 60 * 60 * 1000});
}

export function clearAuthCookie(res) {
    res.clearCookie(AUTH_COOKIE, cookieOptions);
}

export function readToken(req) {
    if (req.cookies?.[AUTH_COOKIE]) {
        return req.cookies[AUTH_COOKIE];
    }

    const header=req.headers.authorization || "";

    if (header.startsWith("Bearer ")) {
        return header.slice(7);
    }

    return null;
}
