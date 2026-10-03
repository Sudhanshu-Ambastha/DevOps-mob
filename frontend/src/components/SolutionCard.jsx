import { formatDate } from "../utils/helpers";

function SolutionCard({solution}) {
    return (
        <article className="solution-card">
            <h3>{solution.title}</h3>
            <p className="muted small">by {solution.author.name} &middot; {formatDate(solution.createdAt)}</p>
            <p>{solution.description}</p>

            <div className="tags">
                {solution.techStack.map((tech) => (
                    <span key={tech} className="tag tag-tech">{tech}</span>
                ))}
            </div>

            {solution.repoUrl && (
                <a href={solution.repoUrl} target="_blank" rel="noreferrer">View source code &rarr;</a>
            )}
        </article>
    );
}

export default SolutionCard;
