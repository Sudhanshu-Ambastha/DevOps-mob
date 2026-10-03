const year=new Date().getFullYear();

function Footer() {
    return (
        <footer className="footer">
            <div className="container footer-inner">
                <p><strong>DevBridge</strong> - connecting real-world problems with developers.</p>
                <p className="muted">College project &copy; {year}</p>
            </div>
        </footer>
    );
}

export default Footer;
