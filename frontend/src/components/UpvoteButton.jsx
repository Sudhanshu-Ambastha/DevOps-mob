function UpvoteButton({count, active, onClick}) {
    return (
        <button
            className={active ? "upvote-button active" : "upvote-button"}
            onClick={onClick}
            title={active ? "Remove upvote" : "Upvote"}
        >
            <span>&#9650;</span>
            {count}
        </button>
    );
}

export default UpvoteButton;
