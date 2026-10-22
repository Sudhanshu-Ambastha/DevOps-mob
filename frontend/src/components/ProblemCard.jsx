import { formatDate, shortText, statusLabel } from "../utils/helpers";

function ProblemCard({ problem, currentUser, onOpen, onUpvote }) {
    const active = currentUser && problem.upvotes.includes(currentUser._id);
    return <article className="problem-card">
        <div className="problem-card-top"><span className="category-label">{problem.category}</span><span className={`status status-${problem.status}`}>{statusLabel(problem.status)}</span></div>
        <button className="problem-card-title" onClick={() => onOpen(problem._id)}>{problem.title}</button>
        <p className="problem-excerpt">{shortText(problem.description, 142)}</p>
        <div className="tags">{problem.tags.slice(0, 3).map((tag) => <span className="tag" key={tag}>{tag}</span>)}</div>
        <div className="problem-card-bottom"><button className={active ? "support-button active" : "support-button"} onClick={() => onUpvote(problem._id)} aria-label={`${active ? "Remove support from" : "Support"} ${problem.title}`}><span>↑</span> {problem.upvotes.length} <small>support</small></button><span className="card-meta">{problem.solutions.length ? `${problem.solutions.length} solution${problem.solutions.length > 1 ? "s" : ""}` : "Seeking solutions"}</span></div>
        <div className="problem-attribution"><span className="avatar">{problem.author.name.charAt(0)}</span><span>{problem.author.name}</span><span>·</span><time>{formatDate(problem.createdAt)}</time>{problem.paid && <span className="budget-mark">Paid · {problem.budget}</span>}</div>
    </article>;
}
export default ProblemCard;
