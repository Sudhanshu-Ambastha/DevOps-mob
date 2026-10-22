function Footer({ onNavigate }) {
    return <footer className="footer"><div className="container-wide footer-inner"><button className="brand footer-brand" onClick={() => onNavigate?.("home")}><span className="brand-mark">d<span>.</span></span><span>devbridge</span></button><p>Real needs. Shared momentum. Useful builds.</p><div><button onClick={() => onNavigate?.("problems")}>Explore problems</button><button onClick={() => onNavigate?.("solutions")}>Solutions</button><button onClick={() => onNavigate?.("submit")}>Share a problem</button></div><small>© 2026 DevBridge · Frontend demonstration</small></div></footer>;
}
export default Footer;
