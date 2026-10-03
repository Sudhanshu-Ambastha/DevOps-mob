import { useState } from "react";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Problems from "./pages/Problems";
import ProblemDetails from "./pages/ProblemDetails";
import SubmitProblem from "./pages/SubmitProblem";
import EditProblem from "./pages/EditProblem";
import MyProblems from "./pages/MyProblems";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import { mockProblems, mockUsers } from "./data/mockData";
import { createId } from "./utils/helpers";

const protectedPages=["submit","edit","my-problems","profile"];

function App() {
    const [problems, setProblems]=useState(mockProblems);
    const [users, setUsers]=useState(mockUsers);
    const [currentUser, setCurrentUser]=useState(null);
    const [page, setPage]=useState("home");
    const [selectedId, setSelectedId]=useState(null);

    const selectedProblem=problems.find((problem) => problem._id === selectedId);

    function navigate(nextPage, problemId=null) {
        setPage(nextPage);
        setSelectedId(problemId);
        window.scrollTo(0, 0);
    }

    function openProblem(problemId) {
        navigate("details", problemId);
    }

    // ---------- Auth ----------

    function login(email, password) {
        const user=users.find((item) => item.email === email.toLowerCase() && item.password === password);

        if (!user) {
            return "Invalid email or password.";
        }

        setCurrentUser(user);

        if (page === "login" || page === "register") {
            navigate("problems");
        }

        return "";
    }

    function register(form) {
        const email=form.email.trim().toLowerCase();

        if (users.some((user) => user.email === email)) {
            return "An account with this email already exists.";
        }

        const newUser={
            _id:createId(),
            name:form.name.trim(),
            email,
            password:form.password,
            role:form.role,
            bio:"",
            skills:[],
            createdAt:new Date().toISOString()
        };

        setUsers([...users, newUser]);
        setCurrentUser(newUser);
        navigate("problems");
        return "";
    }

    function logout() {
        setCurrentUser(null);
        navigate("home");
    }

    function updateProfile(data) {
        const updatedUser={...currentUser,...data};

        setUsers(users.map((user) => user._id === updatedUser._id ? updatedUser : user));
        setCurrentUser(updatedUser);
    }

    // ---------- Problems ----------

    function changeProblem(problemId, getChanges) {
        setProblems(problems.map((problem) => {
            return problem._id === problemId ? {...problem,...getChanges(problem)} : problem;
        }));
    }

    function addProblem(data) {
        const now=new Date().toISOString();

        const newProblem={
            _id:createId(),
            ...data,
            author:{_id:currentUser._id,name:currentUser.name},
            status:"open",
            upvotes:[],
            comments:[],
            solutions:[],
            similarProblems:[],
            embeddingStatus:"not-processed",
            createdAt:now,
            updatedAt:now
        };

        setProblems([newProblem, ...problems]);
        openProblem(newProblem._id);
    }

    function updateProblem(problemId, data) {
        changeProblem(problemId, () => ({...data,updatedAt:new Date().toISOString()}));
        openProblem(problemId);
    }

    function deleteProblem(problemId) {
        setProblems(problems.filter((problem) => problem._id !== problemId));
        navigate("my-problems");
    }

    function toggleUpvote(problemId) {
        if (!currentUser) {
            navigate("login");
            return;
        }

        changeProblem(problemId, (problem) => {
            const hasUpvoted=problem.upvotes.includes(currentUser._id);

            return {
                upvotes:hasUpvoted
                    ? problem.upvotes.filter((userId) => userId !== currentUser._id)
                    : [...problem.upvotes, currentUser._id]
            };
        });
    }

    function addComment(problemId, text) {
        const comment={
            _id:createId(),
            author:{_id:currentUser._id,name:currentUser.name},
            text,
            createdAt:new Date().toISOString()
        };

        changeProblem(problemId, (problem) => ({comments:[...problem.comments, comment]}));
    }

    function addSolution(problemId, data) {
        const solution={
            _id:createId(),
            author:{_id:currentUser._id,name:currentUser.name},
            ...data,
            createdAt:new Date().toISOString()
        };

        changeProblem(problemId, (problem) => ({
            solutions:[...problem.solutions, solution],
            status:problem.status === "open" ? "in-progress" : problem.status
        }));
    }

    // ---------- Pages ----------

    function renderPage() {
        if (protectedPages.includes(page) && !currentUser) {
            return <Login message="Please log in to continue." onLogin={login} onNavigate={navigate} />;
        }

        if (page === "problems") {
            return <Problems problems={problems} currentUser={currentUser} onOpenProblem={openProblem} onUpvote={toggleUpvote} onNavigate={navigate} />;
        }

        if (page === "details") {
            return (
                <ProblemDetails
                    problem={selectedProblem}
                    currentUser={currentUser}
                    onNavigate={navigate}
                    onUpvote={toggleUpvote}
                    onDelete={deleteProblem}
                    onAddComment={addComment}
                    onAddSolution={addSolution}
                />
            );
        }

        if (page === "submit") {
            return <SubmitProblem onSubmit={addProblem} onNavigate={navigate} />;
        }

        if (page === "edit") {
            return <EditProblem problem={selectedProblem} currentUser={currentUser} onUpdate={updateProblem} onNavigate={navigate} />;
        }

        if (page === "my-problems") {
            return <MyProblems problems={problems} currentUser={currentUser} onNavigate={navigate} onOpenProblem={openProblem} onDelete={deleteProblem} />;
        }

        if (page === "profile") {
            return <Profile currentUser={currentUser} problems={problems} onUpdateProfile={updateProfile} />;
        }

        if (page === "login") {
            return <Login onLogin={login} onNavigate={navigate} />;
        }

        if (page === "register") {
            return <Register onRegister={register} onNavigate={navigate} />;
        }

        return <Home problems={problems} currentUser={currentUser} onNavigate={navigate} onOpenProblem={openProblem} onUpvote={toggleUpvote} />;
    }

    return (
        <div className="app">
            <Navbar currentUser={currentUser} currentPage={page} onNavigate={navigate} onLogout={logout} />
            <main className="container main">{renderPage()}</main>
            <Footer />
        </div>
    );
}

export default App;
