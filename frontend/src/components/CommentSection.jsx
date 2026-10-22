import { useState } from "react";
import { formatDate } from "../utils/helpers";

function CommentSection({comments, currentUser, onAddComment, onNavigate}) {
    const [text, setText]=useState("");

    function handleSubmit(event) {
        event.preventDefault();

        if (text.trim() === "") {
            return;
        }

        onAddComment(text.trim());
        setText("");
    }

    return (
        <section className="comment-section">
            <h2>Discussion ({comments.length})</h2>

            {comments.length === 0 && <p className="muted">No comments yet. Start the discussion.</p>}

            <ul className="comment-list">
                {comments.map((comment) => (
                    <li key={comment._id} className="comment">
                        <span className="avatar">{comment.author.name.charAt(0)}</span>
                        <div>
                            <p className="comment-head">
                                <strong>{comment.author.name}</strong>
                                <span className="muted"> &middot; {formatDate(comment.createdAt)}</span>
                            </p>
                            <p>{comment.text}</p>
                        </div>
                    </li>
                ))}
            </ul>

            {currentUser ? (
                <form className="comment-form" onSubmit={handleSubmit}>
                    <textarea
                        rows="3"
                        placeholder="Ask a question or add more details..."
                        value={text}
                        onChange={(event) => setText(event.target.value)}
                    />
                    <button type="submit" className="btn btn-primary" disabled={text.trim() === ""}>Post comment</button>
                </form>
            ) : (
                <p className="muted">
                    <button className="link-button" onClick={() => onNavigate("login")}>Log in</button> to join the discussion.
                </p>
            )}
        </section>
    );
}

export default CommentSection;
