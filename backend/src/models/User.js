import mongoose from "mongoose";
import bcrypt from "bcryptjs";
import env from "../config/env.js";

export const ROLES=["user","developer","admin"];

const userSchema=new mongoose.Schema({
    name:{
        type:String,
        required:[true,"Name is required"],
        trim:true,
        minlength:2,
        maxlength:50
    },
    email:{
        type:String,
        required:[true,"Email is required"],
        unique:true,
        lowercase:true,
        trim:true
    },
    password:{
        type:String,
        required:true,
        select:false
    },
    role:{
        type:String,
        enum:ROLES,
        default:"user"
    },
    bio:{
        type:String,
        trim:true,
        maxlength:300,
        default:""
    },
    skills:{
        type:[String],
        default:[]
    }
},{timestamps:true});

userSchema.pre("save", async function () {
    if (!this.isModified("password")) {
        return;
    }

    this.password=await bcrypt.hash(this.password, env.bcryptRounds);
});

userSchema.methods.comparePassword=function (candidate) {
    return bcrypt.compare(candidate, this.password);
};

userSchema.set("toJSON",{
    transform:(document, output) => {
        delete output.password;
        delete output.__v;
        return output;
    }
});

const User=mongoose.model("User", userSchema);

export default User;
