import mongoose from "mongoose";

const solutionSchema=new mongoose.Schema({
    problem:{
        type:mongoose.Schema.Types.ObjectId,
        ref:"Problem",
        required:true,
        index:true
    },
    author:{
        type:mongoose.Schema.Types.ObjectId,
        ref:"User",
        required:true,
        index:true
    },
    title:{
        type:String,
        required:[true,"Title is required"],
        trim:true,
        minlength:[5,"Title must be at least 5 characters"],
        maxlength:[120,"Title must be at most 120 characters"]
    },
    description:{
        type:String,
        required:[true,"Description is required"],
        trim:true,
        minlength:[20,"Description must be at least 20 characters"],
        maxlength:[5000,"Description must be at most 5000 characters"]
    },
    repoUrl:{type:String,trim:true,default:""},
    demoUrl:{type:String,trim:true,default:""},
    techStack:{type:[String],default:[]},
    isAccepted:{type:Boolean,default:false}
},{timestamps:true});

solutionSchema.index({problem:1,author:1},{unique:true});

const Solution=mongoose.model("Solution", solutionSchema);

export default Solution;
