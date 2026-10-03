import mongoose from "mongoose";

export const CATEGORIES=[
    "education",
    "health",
    "finance",
    "productivity",
    "community",
    "environment",
    "accessibility",
    "transport",
    "agriculture",
    "other"
];

export const STATUSES=["open","in-progress","solved"];

const similarProblemSchema=new mongoose.Schema({
    problem:{type:mongoose.Schema.Types.ObjectId,ref:"Problem"},
    score:{type:Number}
},{_id:false});

const problemSchema=new mongoose.Schema({
    title:{
        type:String,
        required:[true,"Title is required"],
        trim:true,
        minlength:[10,"Title must be at least 10 characters"],
        maxlength:[150,"Title must be at most 150 characters"]
    },
    description:{
        type:String,
        required:[true,"Description is required"],
        trim:true,
        minlength:[30,"Description must be at least 30 characters"],
        maxlength:[5000,"Description must be at most 5000 characters"]
    },
    category:{
        type:String,
        enum:{values:CATEGORIES,message:"Unknown category"},
        default:"other"
    },
    tags:{
        type:[String],
        default:[]
    },
    author:{
        type:mongoose.Schema.Types.ObjectId,
        ref:"User",
        required:true,
        index:true
    },
    status:{
        type:String,
        enum:{values:STATUSES,message:"Unknown status"},
        default:"open"
    },
    upvotes:{
        type:[{type:mongoose.Schema.Types.ObjectId,ref:"User"}],
        default:[]
    },
    upvoteCount:{type:Number,default:0},
    commentCount:{type:Number,default:0},
    solutionCount:{type:Number,default:0},
    embedding:{
        type:[Number],
        select:false
    },
    embeddingModel:{
        type:String,
        select:false
    },
    similarAtSubmission:{
        type:[similarProblemSchema],
        default:[]
    }
},{timestamps:true});

problemSchema.index({createdAt:-1});
problemSchema.index({upvoteCount:-1});
problemSchema.index({tags:1});

const Problem=mongoose.model("Problem", problemSchema);

export default Problem;
