import { useState } from "react";
import { splitList } from "../utils/helpers";

const emptyForm={
    title:"",
    description:"",
    repoUrl:"",
    techStack:""
};

function SolutionForm({onSubmit}) {
    const [form, setForm]=useState(emptyForm);
    const [error, setError]=useState("");

    function handleChange(event) {
        setForm({...form,[event.target.name]:event.target.value});
    }

    function handleSubmit(event) {
        event.preventDefault();

        if (form.title.trim().length < 5 || form.description.trim().length < 20) {
            setError("Please add a title (5+ characters) and a description (20+ characters).");
            return;
        }

        if (form.repoUrl && !form.repoUrl.startsWith("http")) {
            setError("Repository link should start with http:// or https://");
            return;
        }

        onSubmit({
            title:form.title.trim(),
            description:form.description.trim(),
            repoUrl:form.repoUrl.trim(),
            techStack:splitList(form.techStack)
        });

        setForm(emptyForm);
        setError("");
    }

    return (
        <form className="form solution-form" onSubmit={handleSubmit}>
            <h3>Publish your solution</h3>

            <label>
                Solution title
                <input name="title" value={form.title} onChange={handleChange} placeholder="e.g. TeamUp web app" />
            </label>

            <label>
                How does it solve the problem?
                <textarea name="description" rows="4" value={form.description} onChange={handleChange} />
            </label>

            <div className="form-row">
                <label>
                    Repository link
                    <input name="repoUrl" value={form.repoUrl} onChange={handleChange} placeholder="https://github.com/..." />
                </label>

                <label>
                    Tech stack
                    <input name="techStack" value={form.techStack} onChange={handleChange} placeholder="React, Node.js" />
                </label>
            </div>

            {error && <p className="error">{error}</p>}

            <div className="form-actions">
                <button type="submit" className="btn btn-primary">Publish solution</button>
            </div>
        </form>
    );
}

export default SolutionForm;
