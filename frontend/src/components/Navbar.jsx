import { useState } from "react";

function Navbar({currentUser, currentPage, onNavigate, onLogout}) {
    const [menuOpen, setMenuOpen]=useState(false);

    const links=[
        {page:"home",label:"Home"},
        {page:"problems",label:"Browse"},
        {page:"submit",label:"Submit Problem"}
    ];

    if (currentUser) {
        links.push({page:"my-problems",label:"My Problems"});
    }

    function handleClick(page) {
        onNavigate(page);
        setMenuOpen(false);
    }

    return (
        <header className="navbar">
            <div className="container navbar-inner">
                <button className="brand" onClick={() => handleClick("home")}>
                    <span className="brand-logo">DB</span>
                    DevBridge
                </button>

                <button className="menu-button" onClick={() => setMenuOpen(!menuOpen)}>
                    {menuOpen ? "Close" : "Menu"}
                </button>

                <nav className={menuOpen ? "nav-links open" : "nav-links"}>
                    {links.map((link) => (
                        <button
                            key={link.page}
                            className={currentPage === link.page ? "nav-link active" : "nav-link"}
                            onClick={() => handleClick(link.page)}
                        >
                            {link.label}
                        </button>
                    ))}

                    {currentUser ? (
                        <>
                            <button className="nav-user" onClick={() => handleClick("profile")}>
                                <span className="avatar">{currentUser.name.charAt(0)}</span>
                                {currentUser.name.split(" ")[0]}
                            </button>
                            <button className="btn btn-outline btn-small" onClick={onLogout}>Logout</button>
                        </>
                    ) : (
                        <>
                            <button className="nav-link" onClick={() => handleClick("login")}>Login</button>
                            <button className="btn btn-primary btn-small" onClick={() => handleClick("register")}>Register</button>
                        </>
                    )}
                </nav>
            </div>
        </header>
    );
}

export default Navbar;
