import { useState } from "react";
import ProblemCard from "../components/ProblemCard";
import SearchBar from "../components/SearchBar";

function Problems({problems, currentUser, onOpenProblem, onUpvote, onNavigate}) {
    const [query, setQuery]=useState("");
    const [category, setCategory]=useState("");
    const [sortBy, setSortBy]=useState("newest");

    const searchText=query.trim().toLowerCase();

    const filteredProblems=problems.filter((problem) => {
        const matchesCategory=category === "" || problem.category === category;
        const matchesSearch=searchText === ""
            || problem.title.toLowerCase().includes(searchText)
            || problem.description.toLowerCase().includes(searchText)
            || problem.tags.some((tag) => tag.includes(searchText));

        return matchesCategory && matchesSearch;
    });

    const sortedProblems=[...filteredProblems].sort((a, b) => {
        if (sortBy === "upvotes") return b.upvotes.length - a.upvotes.length;
        if (sortBy === "solutions") return b.solutions.length - a.solutions.length;
        return new Date(b.createdAt) - new Date(a.createdAt);
    });

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1>Browse problems</h1>
                    <p className="muted">Find a real problem worth solving.</p>
                </div>
                <button className="btn btn-primary" onClick={() => onNavigate("submit")}>Post a problem</button>
            </div>

            <SearchBar
                query={query}
                category={category}
                sortBy={sortBy}
                onQueryChange={setQuery}
                onCategoryChange={setCategory}
                onSortChange={setSortBy}
            />

            <p className="muted small">Showing {sortedProblems.length} of {problems.length} problems</p>

            {sortedProblems.length === 0 ? (
                <div className="empty">
                    <h3>No problems match your search</h3>
                    <p className="muted">Try another keyword or category.</p>
                </div>
            ) : (
                <div className="problem-grid">
                    {sortedProblems.map((problem) => (
                        <ProblemCard
                            key={problem._id}
                            problem={problem}
                            currentUser={currentUser}
                            onOpen={onOpenProblem}
                            onUpvote={onUpvote}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

export default Problems;
