import { useState } from "react";

function Login({message, onLogin, onNavigate}) {
    const [form, setForm]=useState({email:"",password:""});
    const [error, setError]=useState("");

    function handleChange(event) {
        setForm({...form,[event.target.name]:event.target.value});
    }

    function handleSubmit(event) {
        event.preventDefault();

        if (form.email === "" || form.password === "") {
            setError("Please enter your email and password.");
            return;
        }

        const loginError=onLogin(form.email, form.password);
        setError(loginError);
    }

    return (
        <div className="auth-page">
            <form className="card form auth-card" onSubmit={handleSubmit}>
                <h1>Login</h1>
                {message && <p className="notice">{message}</p>}

                <label>
                    Email
                    <input type="email" name="email" value={form.email} onChange={handleChange} />
                </label>

                <label>
                    Password
                    <input type="password" name="password" value={form.password} onChange={handleChange} />
                </label>

                {error && <p className="error">{error}</p>}

                <button type="submit" className="btn btn-primary btn-full">Login</button>

                <p className="muted small center">
                    New here? <button type="button" className="link-button" onClick={() => onNavigate("register")}>Create an account</button>
                </p>

                <p className="demo-box small">
                    Demo accounts: <strong>riya@devbridge.com / riya123</strong> (user),{" "}
                    <strong>arjun@devbridge.com / arjun123</strong> (developer)
                </p>
            </form>
        </div>
    );
}

export default Login;
