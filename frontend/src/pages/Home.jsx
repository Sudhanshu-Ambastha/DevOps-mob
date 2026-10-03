import ProblemCard from "../components/ProblemCard";

const steps=[
    {title:"Post a problem",text:"Describe a real problem you or your campus faces."},
    {title:"Discuss and upvote",text:"Others upvote and comment so the important problems rise up."},
    {title:"Developers build",text:"Developers publish solutions that anyone can use or improve."}
];

function Home({problems, currentUser, onNavigate, onOpenProblem, onUpvote}) {
    const solutionCount=problems.reduce((total, problem) => total + problem.solutions.length, 0);
    const solvedCount=problems.filter((problem) => problem.status === "solved").length;

    const topProblems=[...problems]
        .sort((a, b) => b.upvotes.length - a.upvotes.length)
        .slice(0, 3);

    return (
        <div>
            <section className="hero">
                <h1>Real problems. Real developers. Real solutions.</h1>
                <p>
                    DevBridge connects people who face everyday problems with developers
                    who can turn them into working projects.
                </p>
                <div className="hero-actions">
                    <button className="btn btn-primary" onClick={() => onNavigate("submit")}>Post a problem</button>
                    <button className="btn btn-outline" onClick={() => onNavigate("problems")}>Browse problems</button>
                </div>
            </section>

            <section className="stats">
                <div className="stat"><strong>{problems.length}</strong><span>Problems posted</span></div>
                <div className="stat"><strong>{solutionCount}</strong><span>Solutions published</span></div>
                <div className="stat"><strong>{solvedCount}</strong><span>Problems solved</span></div>
            </section>

            <section className="section-block">
                <h2>How it works</h2>
                <div className="steps">
                    {steps.map((step, index) => (
                        <div key={step.title} className="card step">
                            <span className="step-number">{index + 1}</span>
                            <h3>{step.title}</h3>
                            <p className="muted">{step.text}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section className="section-block">
                <div className="section-title">
                    <h2>Most upvoted problems</h2>
                    <button className="link-button" onClick={() => onNavigate("problems")}>See all &rarr;</button>
                </div>
                <div className="problem-grid">
                    {topProblems.map((problem) => (
                        <ProblemCard
                            key={problem._id}
                            problem={problem}
                            currentUser={currentUser}
                            onOpen={onOpenProblem}
                            onUpvote={onUpvote}
                        />
                    ))}
                </div>
            </section>
        </div>
    );
}

export default Home;
