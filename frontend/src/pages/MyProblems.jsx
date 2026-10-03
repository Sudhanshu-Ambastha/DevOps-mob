import { formatDate, statusLabel } from "../utils/helpers";

function MyProblems({problems, currentUser, onNavigate, onOpenProblem, onDelete}) {
    const myProblems=problems.filter((problem) => problem.author._id === currentUser._id);

    function handleDelete(problemId) {
        if (window.confirm("Delete this problem? This cannot be undone.")) {
            onDelete(problemId);
        }
    }

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1>My problems</h1>
                    <p className="muted">You have posted {myProblems.length} problem{myProblems.length === 1 ? "" : "s"}.</p>
                </div>
                <button className="btn btn-primary" onClick={() => onNavigate("submit")}>Post a problem</button>
            </div>

            {myProblems.length === 0 ? (
                <div className="empty">
                    <h3>You have not posted any problems yet</h3>
                    <p className="muted">Share a problem from your college or city.</p>
                    <button className="btn btn-primary" onClick={() => onNavigate("submit")}>Post your first problem</button>
                </div>
            ) : (
                <div className="card table-card">
                    {myProblems.map((problem) => (
                        <div key={problem._id} className="row">
                            <div>
                                <h3 className="problem-title" onClick={() => onOpenProblem(problem._id)}>{problem.title}</h3>
                                <p className="muted small">
                                    {formatDate(problem.createdAt)} &middot; {problem.upvotes.length} upvotes &middot; {problem.solutions.length} solutions
                                </p>
                            </div>
                            <div className="row-actions">
                                <span className={"status status-" + problem.status}>{statusLabel(problem.status)}</span>
                                <button className="btn btn-outline btn-small" onClick={() => onNavigate("edit", problem._id)}>Edit</button>
                                <button className="btn btn-danger btn-small" onClick={() => handleDelete(problem._id)}>Delete</button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default MyProblems;
