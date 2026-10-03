import ProblemForm from "../components/ProblemForm";

function EditProblem({problem, currentUser, onUpdate, onNavigate}) {
    if (!problem || problem.author._id !== currentUser._id) {
        return (
            <div className="empty">
                <h3>You can only edit your own problems</h3>
                <button className="btn btn-primary" onClick={() => onNavigate("my-problems")}>Go to My Problems</button>
            </div>
        );
    }

    return (
        <div className="narrow">
            <div className="page-header">
                <div>
                    <h1>Edit problem</h1>
                    <p className="muted">Update the details or mark the problem as solved.</p>
                </div>
            </div>

            <ProblemForm
                initialProblem={problem}
                submitLabel="Save changes"
                showStatus={true}
                onSubmit={(data) => onUpdate(problem._id, data)}
                onCancel={() => onNavigate("details", problem._id)}
            />
        </div>
    );
}

export default EditProblem;
