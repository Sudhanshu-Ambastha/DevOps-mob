import UpvoteButton from "../components/UpvoteButton";
import CommentSection from "../components/CommentSection";
import SolutionCard from "../components/SolutionCard";
import SolutionForm from "../components/SolutionForm";
import { formatDate, statusLabel } from "../utils/helpers";

function ProblemDetails({problem, currentUser, onNavigate, onUpvote, onDelete, onAddComment, onAddSolution}) {
    if (!problem) {
        return (
            <div className="empty">
                <h3>Problem not found</h3>
                <button className="btn btn-primary" onClick={() => onNavigate("problems")}>Back to problems</button>
            </div>
        );
    }

    const isAuthor=currentUser && currentUser._id === problem.author._id;
    const isDeveloper=currentUser && currentUser.role === "developer";
    const hasUpvoted=currentUser ? problem.upvotes.includes(currentUser._id) : false;

    function handleDelete() {
        if (window.confirm("Delete this problem? This cannot be undone.")) {
            onDelete(problem._id);
        }
    }

    return (
        <div className="details">
            <button className="link-button" onClick={() => onNavigate("problems")}>&larr; Back to problems</button>

            <article className="card section">
                <div className="details-header">
                    <UpvoteButton
                        count={problem.upvotes.length}
                        active={hasUpvoted}
                        onClick={() => onUpvote(problem._id)}
                    />

                    <div>
                        <div className="card-top">
                            <span className="category">{problem.category}</span>
                            <span className={"status status-" + problem.status}>{statusLabel(problem.status)}</span>
                        </div>
                        <h1>{problem.title}</h1>
                        <p className="muted small">
                            Posted by {problem.author.name} on {formatDate(problem.createdAt)}
                            {problem.updatedAt !== problem.createdAt && " · updated " + formatDate(problem.updatedAt)}
                        </p>
                    </div>
                </div>

                <p className="description">{problem.description}</p>

                <div className="tags">
                    {problem.tags.map((tag) => (
                        <span key={tag} className="tag">#{tag}</span>
                    ))}
                </div>

                {isAuthor && (
                    <div className="owner-actions">
                        <button className="btn btn-outline btn-small" onClick={() => onNavigate("edit", problem._id)}>Edit</button>
                        <button className="btn btn-danger btn-small" onClick={handleDelete}>Delete</button>
                    </div>
                )}
            </article>

            <section className="card section">
                <h2>Solutions ({problem.solutions.length})</h2>

                {problem.solutions.length === 0 && <p className="muted">No solutions yet.</p>}

                {problem.solutions.map((solution) => (
                    <SolutionCard key={solution._id} solution={solution} />
                ))}

                {isDeveloper && <SolutionForm onSubmit={(data) => onAddSolution(problem._id, data)} />}

                {currentUser && !isDeveloper && (
                    <p className="muted small">Only developers can publish solutions. You can change your role in your profile.</p>
                )}

                {!currentUser && (
                    <p className="muted small">
                        <button className="link-button" onClick={() => onNavigate("login")}>Log in</button> as a developer to publish a solution.
                    </p>
                )}
            </section>

            <CommentSection
                comments={problem.comments}
                currentUser={currentUser}
                onAddComment={(text) => onAddComment(problem._id, text)}
                onNavigate={onNavigate}
            />
        </div>
    );
}

export default ProblemDetails;
