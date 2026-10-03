import { useState } from "react";
import { formatDate, splitList } from "../utils/helpers";

function Profile({currentUser, problems, onUpdateProfile}) {
    const [form, setForm]=useState({
        name:currentUser.name,
        bio:currentUser.bio,
        skills:currentUser.skills.join(", "),
        role:currentUser.role
    });
    const [message, setMessage]=useState("");

    const myProblems=problems.filter((problem) => problem.author._id === currentUser._id);
    const upvotesReceived=myProblems.reduce((total, problem) => total + problem.upvotes.length, 0);
    const solutionsPublished=problems.reduce((total, problem) => {
        return total + problem.solutions.filter((solution) => solution.author._id === currentUser._id).length;
    }, 0);

    function handleChange(event) {
        setForm({...form,[event.target.name]:event.target.value});
        setMessage("");
    }

    function handleSubmit(event) {
        event.preventDefault();

        if (form.name.trim().length < 2) {
            setMessage("Name should be at least 2 characters.");
            return;
        }

        onUpdateProfile({
            name:form.name.trim(),
            bio:form.bio.trim(),
            skills:splitList(form.skills),
            role:form.role
        });

        setMessage("Profile saved.");
    }

    return (
        <div className="narrow">
            <div className="card profile-header">
                <span className="avatar avatar-large">{currentUser.name.charAt(0)}</span>
                <div>
                    <h1>{currentUser.name}</h1>
                    <p className="muted">
                        {currentUser.email} &middot; {currentUser.role} &middot; joined {formatDate(currentUser.createdAt)}
                    </p>
                </div>
            </div>

            <section className="stats">
                <div className="stat"><strong>{myProblems.length}</strong><span>Problems posted</span></div>
                <div className="stat"><strong>{upvotesReceived}</strong><span>Upvotes received</span></div>
                <div className="stat"><strong>{solutionsPublished}</strong><span>Solutions published</span></div>
            </section>

            <form className="card form" onSubmit={handleSubmit}>
                <h2>Edit profile</h2>

                <label>
                    Name
                    <input name="name" value={form.name} onChange={handleChange} />
                </label>

                <label>
                    Bio
                    <textarea name="bio" rows="3" value={form.bio} onChange={handleChange} />
                </label>

                <label>
                    Skills
                    <input name="skills" value={form.skills} onChange={handleChange} placeholder="Comma separated, e.g. React, Python" />
                </label>

                <label>
                    Role
                    <select name="role" value={form.role} onChange={handleChange}>
                        <option value="user">User</option>
                        <option value="developer">Developer</option>
                    </select>
                </label>

                {message && <p className="notice">{message}</p>}

                <div className="form-actions">
                    <button type="submit" className="btn btn-primary">Save profile</button>
                </div>
            </form>
        </div>
    );
}

export default Profile;
