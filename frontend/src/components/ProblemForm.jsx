import { useState } from "react";
import { CATEGORIES, STATUSES } from "../data/mockData";
import { splitList, statusLabel } from "../utils/helpers";

function ProblemForm({initialProblem, submitLabel, showStatus, onSubmit, onCancel}) {
    const [form, setForm]=useState({
        title:initialProblem ? initialProblem.title : "",
        description:initialProblem ? initialProblem.description : "",
        category:initialProblem ? initialProblem.category : CATEGORIES[0],
        tags:initialProblem ? initialProblem.tags.join(", ") : "",
        status:initialProblem ? initialProblem.status : "open"
    });
    const [errors, setErrors]=useState({});

    function handleChange(event) {
        setForm({...form,[event.target.name]:event.target.value});
    }

    function validate() {
        const newErrors={};

        if (form.title.trim().length < 10) {
            newErrors.title="Title should be at least 10 characters.";
        }

        if (form.description.trim().length < 30) {
            newErrors.description="Description should be at least 30 characters.";
        }

        return newErrors;
    }

    function handleSubmit(event) {
        event.preventDefault();

        const newErrors=validate();
        setErrors(newErrors);

        if (Object.keys(newErrors).length > 0) {
            return;
        }

        const problemData={
            title:form.title.trim(),
            description:form.description.trim(),
            category:form.category,
            tags:splitList(form.tags.toLowerCase())
        };

        if (showStatus) {
            problemData.status=form.status;
        }

        onSubmit(problemData);
    }

    return (
        <form className="card form" onSubmit={handleSubmit}>
            <label>
                Title
                <input
                    name="title"
                    value={form.title}
                    onChange={handleChange}
                    placeholder="e.g. Students cannot find teammates for projects"
                />
                {errors.title && <span className="error">{errors.title}</span>}
            </label>

            <label>
                Description
                <textarea
                    name="description"
                    rows="6"
                    value={form.description}
                    onChange={handleChange}
                    placeholder="Who faces this problem? What happens today? Why is it a problem?"
                />
                <span className="hint">{form.description.length} characters</span>
                {errors.description && <span className="error">{errors.description}</span>}
            </label>

            <div className="form-row">
                <label>
                    Category
                    <select name="category" value={form.category} onChange={handleChange}>
                        {CATEGORIES.map((item) => (
                            <option key={item} value={item}>{item}</option>
                        ))}
                    </select>
                </label>

                {showStatus && (
                    <label>
                        Status
                        <select name="status" value={form.status} onChange={handleChange}>
                            {STATUSES.map((item) => (
                                <option key={item} value={item}>{statusLabel(item)}</option>
                            ))}
                        </select>
                    </label>
                )}
            </div>

            <label>
                Tags
                <input
                    name="tags"
                    value={form.tags}
                    onChange={handleChange}
                    placeholder="Comma separated, e.g. hostel, booking"
                />
            </label>

            <div className="form-actions">
                {onCancel && <button type="button" className="btn btn-outline" onClick={onCancel}>Cancel</button>}
                <button type="submit" className="btn btn-primary">{submitLabel}</button>
            </div>
        </form>
    );
}

export default ProblemForm;
