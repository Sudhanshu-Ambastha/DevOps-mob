import { useState } from "react";

function Icon({ name }) {
    const paths = { sun: <><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/></>, moon: <path d="M20.9 13A9 9 0 0 1 11 3.1 9 9 0 1 0 20.9 13Z"/>, bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></>, grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></> };
    return <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

function Navbar({ currentUser, currentPage, onNavigate, onLogout, theme, onToggleTheme, followedCount = 0 }) {
    const [open, setOpen] = useState(false); const [menu, setMenu] = useState("");
    const go = (page, id) => { onNavigate(page, id); setOpen(false); setMenu(""); };
    const active = currentPage === "details" ? "problems" : currentPage === "solution-details" ? "solutions" : currentPage;
    return <header className="navbar"><div className="nav-inner">
        <button className="brand" onClick={() => go("home")} aria-label="DevBridge home"><span className="brand-mark"><svg viewBox="0 0 28 28" aria-hidden="true"><path d="M5 20.5V7.7h5.6c4.4 0 7.2 2.4 7.2 6.4 0 3.9-2.8 6.4-7.2 6.4H5Zm5.3-3c2.4 0 3.8-1.2 3.8-3.4s-1.4-3.4-3.8-3.4H8.6v6.8h1.7ZM20.2 20.5V7.7H23v12.8h-2.8Z" fill="currentColor"/><circle cx="21.6" cy="23" r="1.7" fill="#54e1b3"/></svg></span><span>devbridge</span><span className="brand-beta">COMMUNITY</span></button>
        <button className="menu-toggle" onClick={() => setOpen(!open)} aria-expanded={open} aria-label="Toggle navigation"><span/><span/><span/></button>
        <nav className={open ? "nav-links is-open" : "nav-links"} aria-label="Main navigation">
            <button className={active === "problems" ? "nav-link active" : "nav-link"} onClick={() => go("problems")}>Explore problems</button>
            <button className={active === "solutions" ? "nav-link active" : "nav-link"} onClick={() => go("solutions")}>Solutions</button>
            <button className="nav-link" onClick={() => { go("home"); setTimeout(() => document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" }), 80); }}>How it works</button>
            {currentUser && <button className={currentPage === "dashboard" ? "nav-link active" : "nav-link"} onClick={() => go("dashboard", "overview")}>Dashboard</button>}
            <span className="nav-spacer"/>
            <button className="icon-button theme-button" onClick={onToggleTheme} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`} title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}><Icon name={theme === "dark" ? "sun" : "moon"}/></button>
            {currentUser ? <>
                <div className="nav-popover-wrap"><button className={`icon-button ${menu === "activity" ? "selected" : ""}`} onClick={() => setMenu(menu === "activity" ? "" : "activity")} aria-label="Activity"><Icon name="bell"/>{followedCount > 0 && <i className="notification-dot"/>}</button>{menu === "activity" && <div className="nav-popover activity-popover"><span className="eyebrow">ACTIVITY</span><strong>{followedCount ? `${followedCount} followed request${followedCount === 1 ? "" : "s"}` : "You're all caught up"}</strong><p>{followedCount ? "Followed problems are waiting in your dashboard." : "Follow a problem to keep its activity close."}</p><button className="text-link" onClick={() => go("dashboard", "activity")}>Open activity →</button></div>}</div>
                <div className="nav-popover-wrap"><button className={`account-trigger ${menu === "account" ? "selected" : ""}`} onClick={() => setMenu(menu === "account" ? "" : "account")} aria-expanded={menu === "account"}><span className="avatar">{currentUser.name?.charAt(0)}</span><span className="account-name">{currentUser.name?.split(" ")[0]}<small>DEMO SESSION</small></span><span className="chevron">⌄</span></button>{menu === "account" && <div className="nav-popover account-popover"><button onClick={() => go("dashboard", "overview")}><Icon name="grid"/> Dashboard</button><button onClick={() => go("dashboard", "profile")}>Profile & settings</button><button onClick={() => { onLogout(); setMenu(""); }}>Exit demo session</button></div>}</div>
            </> : <><button className="nav-link sign-in-link" onClick={() => go("login")}>Sign in</button><button className="btn btn-primary btn-small" onClick={() => go("register")}>Get started <span>↗</span></button></>}
            <button className="btn btn-share" onClick={() => go("submit")}><span className="share-plus">+</span> Share a problem</button>
        </nav>
    </div></header>;
}
export default Navbar;
