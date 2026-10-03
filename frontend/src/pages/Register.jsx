import { useState } from "react";

function Register({onRegister, onNavigate}) {
    const [form, setForm]=useState({
        name:"",
        email:"",
        password:"",
        role:"user"
    });
    const [error, setError]=useState("");

    function handleChange(event) {
        setForm({...form,[event.target.name]:event.target.value});
    }

    function handleSubmit(event) {
        event.preventDefault();

        if (form.name.trim().length < 2) {
            setError("Please enter your name.");
            return;
        }

        if (!form.email.includes("@")) {
            setError("Please enter a valid email.");
            return;
        }

        if (form.password.length < 6) {
            setError("Password should be at least 6 characters.");
            return;
        }

        const registerError=onRegister(form);
        setError(registerError);
    }

    return (
        <div className="auth-page">
            <form className="card form auth-card" onSubmit={handleSubmit}>
                <h1>Create account</h1>

                <label>
                    Full name
                    <input name="name" value={form.name} onChange={handleChange} />
                </label>

                <label>
                    Email
                    <input type="email" name="email" value={form.email} onChange={handleChange} />
                </label>

                <label>
                    Password
                    <input type="password" name="password" value={form.password} onChange={handleChange} />
                </label>

                <div className="role-options">
                    <label className={form.role === "user" ? "role-option selected" : "role-option"}>
                        <input type="radio" name="role" value="user" checked={form.role === "user"} onChange={handleChange} />
                        <strong>I have problems</strong>
                        <span className="muted small">Post, upvote and discuss</span>
                    </label>

                    <label className={form.role === "developer" ? "role-option selected" : "role-option"}>
                        <input type="radio" name="role" value="developer" checked={form.role === "developer"} onChange={handleChange} />
                        <strong>I am a developer</strong>
                        <span className="muted small">Also publish solutions</span>
                    </label>
                </div>

                {error && <p className="error">{error}</p>}

                <button type="submit" className="btn btn-primary btn-full">Register</button>

                <p className="muted small center">
                    Already have an account? <button type="button" className="link-button" onClick={() => onNavigate("login")}>Login</button>
                </p>
            </form>
        </div>
    );
}

export default Register;
