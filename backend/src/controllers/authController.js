import User from "../models/User.js";
import ApiError from "../utils/ApiError.js";
import { validateLogin, validateRegister } from "../utils/validators.js";
import { clearAuthCookie, setAuthCookie, signToken } from "../utils/token.js";

export async function register(req, res) {
    const data=validateRegister(req.body);

    if (await User.exists({email:data.email})) {
        throw new ApiError(409, "An account with this email already exists");
    }

    const user=await User.create(data);

    setAuthCookie(res, signToken(user._id));
    res.status(201).json({user});
}

export async function login(req, res) {
    const {email, password}=validateLogin(req.body);
    const user=await User.findOne({email}).select("+password");

    if (!user || !(await user.comparePassword(password))) {
        throw new ApiError(401, "Invalid email or password");
    }

    setAuthCookie(res, signToken(user._id));
    res.json({user});
}

export function logout(req, res) {
    clearAuthCookie(res);
    res.json({message:"Logged out"});
}

export function currentUser(req, res) {
    res.json({user:req.user});
}
