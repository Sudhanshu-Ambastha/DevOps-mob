import { useEffect, useMemo, useState } from "react";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Problems from "./pages/Problems";
import ProblemDetails from "./pages/ProblemDetails";
import SubmitProblem from "./pages/SubmitProblem";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import Solutions from "./pages/Solutions";
import SolutionDetails from "./pages/SolutionDetails";
import { mockProblems, mockUsers } from "./data/mockData";
import { createId } from "./utils/helpers";

function readRoute() {
    const path = window.location.pathname.split("/").filter(Boolean);
    const query = new URLSearchParams(window.location.search).get("q") || "";
    if (!path.length) return { page: "home", id: null, query };
    if (path[0] === "problems" && path[1]) return { page: "details", id: path[1], query };
    if (path[0] === "problems") return { page: "problems", id: null, query };
    if (path[0] === "solutions" && path[1]) return { page: "solution-details", id: path[1], query };
    if (path[0] === "solutions") return { page: "solutions", id: null, query };
    if (path[0] === "submit") return { page: "submit", id: null, query };
    if (path[0] === "dashboard") return { page: "dashboard", id: path[1] || "overview", query };
    if (path[0] === "profile") return { page: "dashboard", id: "profile", query };
    if (path[0] === "login" || path[0] === "register") return { page: path[0], id: null, query };
    return { page: "home", id: null, query };
}

function routePath(page, id) {
    if (page === "profile") return "/dashboard/profile";
    if (page === "details") return `/problems/${encodeURIComponent(id)}`;
    if (page === "solution-details") return `/solutions/${encodeURIComponent(id)}`;
    if (page === "dashboard") return `/dashboard/${encodeURIComponent(id || "overview")}`;
    return ({ home: "/", problems: "/problems", submit: "/submit", solutions: "/solutions", login: "/login", register: "/register" })[page] || "/";
}

function App() {
    const [problems, setProblems] = useState(mockProblems);
    const [currentUser, setCurrentUser] = useState(null);
    const [route, setRoute] = useState(readRoute);
    const [followed, setFollowed] = useState([]);
    const [theme, setTheme] = useState(() => {
        try { return localStorage.getItem("devbridge-theme") === "light" ? "light" : "dark"; }
        catch { return "dark"; }
    });
    const selectedProblem = problems.find((problem) => problem._id === route.id);
    const allSolutions = useMemo(() => problems.flatMap((problem) => problem.solutions.map((solution) => ({ ...solution, problemId: problem._id, problemTitle: problem.title }))), [problems]);
    const selectedSolution = allSolutions.find((solution) => solution._id === route.id);

    useEffect(() => {
        const syncRoute = () => setRoute(readRoute());
        window.addEventListener("popstate", syncRoute);
        return () => window.removeEventListener("popstate", syncRoute);
    }, []);
    useEffect(() => {
        document.documentElement.dataset.theme = theme;
        try { localStorage.setItem("devbridge-theme", theme); } catch { /* Theme still works for this session. */ }
    }, [theme]);

    function navigate(nextPage, id = null) {
        const path = routePath(nextPage, id);
        const queryString = nextPage === "problems" && typeof id === "string" && id ? `?q=${encodeURIComponent(id)}` : "";
        window.history.pushState({}, "", `${path}${queryString}`);
        setRoute({ page: nextPage === "profile" ? "dashboard" : nextPage, id: nextPage === "profile" ? "profile" : nextPage === "dashboard" ? id || "overview" : nextPage === "problems" && typeof id === "string" ? null : id, query: nextPage === "problems" && typeof id === "string" ? id : "" });
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function changeProblem(id, mutate) {
        setProblems((current) => current.map((item) => item._id === id ? mutate(item) : item));
    }
    function enterDemo() {
        setCurrentUser({ ...mockUsers[1], demo: true });
        navigate("dashboard", "overview");
    }
    function register(form) {
        setCurrentUser({ _id: createId(), name: form.name.trim(), email: form.email.trim().toLowerCase(), role: form.role, bio: "", skills: [], demo: true });
        navigate("dashboard", "overview");
    }
    function addProblem(data) {
        const id = createId();
        const item = { _id: id, ...data, author: { _id: currentUser?._id ?? "guest", name: currentUser?.name ?? "Community member" }, status: "open", upvotes: [], comments: [], solutions: [], similarProblems: [], createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
        setProblems((current) => [item, ...current]);
        navigate("details", id);
    }
    function upvote(id) {
        if (!currentUser) return navigate("login");
        changeProblem(id, (item) => ({ ...item, upvotes: item.upvotes.includes(currentUser._id) ? item.upvotes.filter((uid) => uid !== currentUser._id) : [...item.upvotes, currentUser._id] }));
    }
    function addComment(id, text) {
        if (!currentUser) return navigate("login");
        changeProblem(id, (item) => ({ ...item, comments: [...item.comments, { _id: createId(), author: { _id: currentUser._id, name: currentUser.name }, text, createdAt: new Date().toISOString() }] }));
    }
    function toggleFollow(id) {
        if (!currentUser) return navigate("login");
        setFollowed((ids) => ids.includes(id) ? ids.filter((value) => value !== id) : [...ids, id]);
    }
    function addSolution(id, data) {
        if (!currentUser) return navigate("login");
        const solution = { _id: createId(), author: { _id: currentUser._id, name: currentUser.name }, ...data, techStack: data.techStack ?? [], features: data.features ?? [], createdAt: new Date().toISOString() };
        changeProblem(id, (item) => ({ ...item, solutions: [...item.solutions, solution], status: "in-progress" }));
    }
    function updateProfile(data) { setCurrentUser((user) => ({ ...user, ...data })); }
    function signOut() { setCurrentUser(null); setFollowed([]); navigate("home"); }

    let content;
    if (route.page === "problems") content = <Problems problems={problems} currentUser={currentUser} initialQuery={route.query} onOpenProblem={(id) => navigate("details", id)} onUpvote={upvote} onNavigate={navigate} />;
    else if (route.page === "details") content = <ProblemDetails problem={selectedProblem} allProblems={problems} currentUser={currentUser} followed={followed.includes(route.id)} onNavigate={navigate} onUpvote={upvote} onAddComment={addComment} onAddSolution={addSolution} onFollow={toggleFollow} />;
    else if (route.page === "submit") content = <SubmitProblem problems={problems} onSubmit={addProblem} onNavigate={navigate} />;
    else if (route.page === "solutions") content = <Solutions solutions={allSolutions} onNavigate={navigate} />;
    else if (route.page === "solution-details") content = <SolutionDetails solution={selectedSolution} onNavigate={navigate} />;
    else if (route.page === "dashboard") content = currentUser ? <Profile currentUser={currentUser} problems={problems} followed={followed} section={route.id} onNavigate={navigate} onUpdateProfile={updateProfile} onSignOut={signOut} /> : <Login onDemo={enterDemo} onNavigate={navigate} />;
    else if (route.page === "login") content = <Login onDemo={enterDemo} onNavigate={navigate} />;
    else if (route.page === "register") content = <Register onRegister={register} onNavigate={navigate} />;
    else content = <Home problems={problems} currentUser={currentUser} onNavigate={navigate} onOpenProblem={(id) => navigate("details", id)} onUpvote={upvote} />;

    return <div className={`app theme-${theme}`}><Navbar currentUser={currentUser} currentPage={route.page} onNavigate={navigate} onLogout={signOut} theme={theme} onToggleTheme={() => setTheme((current) => current === "dark" ? "light" : "dark")} followedCount={followed.length} /><main className="main" key={`${route.page}-${route.id || ""}`}>{content}</main><Footer onNavigate={navigate} /></div>;
}

export default App;
