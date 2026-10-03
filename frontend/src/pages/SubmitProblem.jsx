import ProblemForm from "../components/ProblemForm";

function SubmitProblem({onSubmit, onNavigate}) {
    return (
        <div className="narrow">
            <div className="page-header">
                <div>
                    <h1>Submit a problem</h1>
                    <p className="muted">Explain the problem clearly. Developers will take it from there.</p>
                </div>
            </div>

            <ProblemForm
                submitLabel="Submit problem"
                onSubmit={onSubmit}
                onCancel={() => onNavigate("problems")}
            />
        </div>
    );
}

export default SubmitProblem;
