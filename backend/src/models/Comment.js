import mongoose from "mongoose";

const commentSchema=new mongoose.Schema({
    problem:{
        type:mongoose.Schema.Types.ObjectId,
        ref:"Problem",
        required:true,
        index:true
    },
    author:{
        type:mongoose.Schema.Types.ObjectId,
        ref:"User",
        required:true
    },
    body:{
        type:String,
        required:[true,"Comment cannot be empty"],
        trim:true,
        maxlength:[1000,"Comment must be at most 1000 characters"]
    },
    edited:{type:Boolean,default:false}
},{timestamps:true});

const Comment=mongoose.model("Comment", commentSchema);

export default Comment;
