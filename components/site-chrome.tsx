import Link from "next/link";

const navigation = [
  { href: "/birth-chart", label: "Birth chart" },
  { href: "/explore", label: "Explore" },
  { href: "/guide", label: "The guide" },
];

export function Header() {
  return (
    <header className="site-header">
      <div className="page-container header-inner">
        <Link aria-label="Nakshatra AI home" className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">✳</span>
          <span className="brand-name">nakshatra<span>ai</span></span>
        </Link>
        <nav aria-label="Main navigation" className="main-nav">
          {navigation.map((item) => <Link href={item.href} key={item.href}>{item.label}</Link>)}
        </nav>
        <div className="header-actions">
          <Link className="header-dashboard" href="/dashboard">My space <span aria-hidden="true">↗</span></Link>
          <Link className="header-cta" href="/birth-chart">Get started <span aria-hidden="true">↗</span></Link>
        </div>
        <Link aria-label="Start your birth chart" className="mobile-header-cta" href="/birth-chart">Start <span aria-hidden="true">↗</span></Link>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="page-container footer-main">
        <div className="footer-brand">
          <Link aria-label="Nakshatra AI home" className="brand" href="/">
            <span className="brand-mark" aria-hidden="true">✳</span>
            <span className="brand-name">nakshatra<span>ai</span></span>
          </Link>
          <p>Ancient wisdom, clearly explained.<br />A thoughtful space to explore Jyotisha.</p>
        </div>
        <div className="footer-links">
          <div><span className="footer-heading">Explore</span><Link href="/birth-chart">Birth chart</Link><Link href="/explore">Life themes</Link><Link href="/guide">The guide</Link></div>
          <div><span className="footer-heading">Your space</span><Link href="/dashboard">Dashboard</Link><a href="mailto:hello@nakshatra.ai">Get in touch</a></div>
        </div>
      </div>
      <div className="page-container footer-bottom">
        <span>© {new Date().getFullYear()} Nakshatra AI</span>
        <span>For reflection and learning. Not a substitute for professional advice.</span>
        <span>Made with intention <b aria-hidden="true">✦</b></span>
      </div>
    </footer>
  );
}
