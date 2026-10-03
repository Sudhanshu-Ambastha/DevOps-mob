import UpvoteButton from "./UpvoteButton";
import { formatDate, shortText, statusLabel } from "../utils/helpers";

function ProblemCard({problem, currentUser, onOpen, onUpvote}) {
    const hasUpvoted=currentUser ? problem.upvotes.includes(currentUser._id) : false;

    return (
        <article className="card problem-card">
            <div className="card-top">
                <span className="category">{problem.category}</span>
                <span className={"status status-" + problem.status}>{statusLabel(problem.status)}</span>
            </div>

            <h3 className="problem-title" onClick={() => onOpen(problem._id)}>{problem.title}</h3>
            <p className="muted">{shortText(problem.description, 140)}</p>

            <div className="tags">
                {problem.tags.map((tag) => (
                    <span key={tag} className="tag">#{tag}</span>
                ))}
            </div>

            <div className="card-footer">
                <UpvoteButton
                    count={problem.upvotes.length}
                    active={hasUpvoted}
                    onClick={() => onUpvote(problem._id)}
                />
                <span className="meta">{problem.comments.length} comments</span>
                <span className="meta">{problem.solutions.length} solutions</span>
                <span className="meta author">by {problem.author.name} &middot; {formatDate(problem.createdAt)}</span>
            </div>
        </article>
    );
}

export default ProblemCard;
