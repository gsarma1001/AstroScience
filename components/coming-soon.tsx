import Link from "next/link";

type ComingSoonProps = {
  kicker: string;
  title: string;
  description: string;
};

export function ComingSoon({ kicker, title, description }: ComingSoonProps) {
  return (
    <main className="coming-soon page-container">
      <div className="coming-soon-mark" aria-hidden="true">✳</div>
      <span className="section-kicker">{kicker}</span>
      <h1>{title}</h1>
      <p>{description}</p>
      <span className="coming-soon-label">DEVELOPMENT PLACEHOLDER</span>
      <Link className="button button-gold" href="/">Return home <span aria-hidden="true">↗</span></Link>
    </main>
  );
}
