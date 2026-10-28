import Link from "next/link";
import { Footer, Header } from "@/components/site-chrome";
import { SectionHeading } from "@/components/section-heading";

const features = [
  {
    number: "01",
    title: "Your birth chart",
    description:
      "A clear starting point for understanding the planetary placements at the moment you were born.",
    icon: "◉",
  },
  {
    number: "02",
    title: "Planetary periods",
    description:
      "Explore the traditional timing systems that bring different themes into focus throughout life.",
    icon: "↗",
  },
  {
    number: "03",
    title: "Conversations that clarify",
    description:
      "Ask thoughtful questions and get grounded explanations of Jyotisha concepts in everyday language.",
    icon: "✳",
  },
];

const lifeAreas = [
  ["01", "Work & purpose", "Your strengths, direction, and relationship with meaningful work."],
  ["02", "Relationships", "The ways you connect, communicate, and grow alongside others."],
  ["03", "Personal growth", "Patterns, possibilities, and invitations to know yourself more deeply."],
  ["04", "Wellbeing", "Traditional perspectives on balance, energy, and everyday rhythms."],
];

export default function HomePage() {
  return (
    <>
      <Header />
      <main>
        <section className="hero">
          <div className="hero-inner page-container">
            <div className="hero-copy">
              <span className="eyebrow"><span className="eyebrow-dot" /> A more thoughtful way to explore Jyotisha</span>
              <h1>Discover Your<br /><em>Cosmic Blueprint</em></h1>
              <p className="hero-description">
                Explore your Vedic birth chart, understand your planetary periods, and discover traditional Jyotisha interpretations of your life&apos;s journey.
              </p>
              <div className="hero-actions">
                <Link className="button button-gold" href="/birth-chart">
                  Explore My Birth Chart <span aria-hidden="true">↗</span>
                </Link>
                <a className="text-link" href="#how-it-works">See how it works <span aria-hidden="true">↓</span></a>
              </div>
              <div className="hero-note">
                <span className="note-star" aria-hidden="true">✦</span>
                Rooted in tradition. Designed for today.
              </div>
            </div>
            <div className="hero-art" aria-label="Minimal illustration of a Vedic chart and celestial orbit" role="img">
              <div className="art-glow" />
              <div className="orbit orbit-one" />
              <div className="orbit orbit-two" />
              <div className="orbit orbit-three" />
              <div className="art-star star-one">✦</div>
              <div className="art-star star-two">✧</div>
              <div className="art-star star-three">·</div>
              <div className="chart-card">
                <span className="chart-caption">THE CELESTIAL MAP</span>
                <svg className="chart-svg" viewBox="0 0 300 300" fill="none" aria-hidden="true">
                  <rect x="20" y="20" width="260" height="260" rx="4" stroke="currentColor" strokeOpacity=".44" />
                  <path d="M20 20L280 280M280 20L20 280M150 20V280M20 150H280M150 20L20 150L150 280L280 150L150 20Z" stroke="currentColor" strokeOpacity=".3" />
                  <circle cx="150" cy="150" r="52" stroke="currentColor" strokeOpacity=".52" />
                  <circle cx="150" cy="150" r="5" fill="#D9B76E" />
                  <circle cx="150" cy="39" r="3" fill="#D9B76E" />
                  <circle cx="257" cy="150" r="3" fill="#D9B76E" />
                  <circle cx="42" cy="150" r="3" fill="#D9B76E" />
                  <circle cx="150" cy="260" r="3" fill="#D9B76E" />
                  <path d="M150 48V98M202 150H252M48 150H98M150 202V252" stroke="currentColor" strokeOpacity=".22" strokeDasharray="2 7" />
                </svg>
                <div className="chart-label chart-label-top">LAGNA</div>
                <div className="chart-label chart-label-left">RASHI</div>
                <div className="chart-label chart-label-right">GRAHA</div>
                <div className="chart-label chart-label-bottom">BHAVA</div>
                <span className="chart-placeholder">A chart begins with your birth details</span>
              </div>
              <span className="art-index">01 — YOUR MAP, YOUR STORY</span>
            </div>
          </div>
          <div className="hero-bottom page-container">
            <span>ANCIENT WISDOM, CLEARLY EXPLAINED</span>
            <span className="hero-bottom-line" />
            <span>01 / 04</span>
          </div>
        </section>

        <section className="section how-section" id="how-it-works">
          <div className="page-container">
            <SectionHeading
              kicker="A simple beginning"
              title={<>A little context.<br /><em>A lot more clarity.</em></>}
              description="Jyotisha can feel like a world of its own. We make it easier to begin, one considered step at a time."
            />
            <div className="steps-grid">
              <article className="step-card">
                <span className="step-number">01</span>
                <div className="step-icon"><span>◷</span></div>
                <h3>Share your details</h3>
                <p>Start with your birth date, time, and place. These details shape the foundation of a Vedic chart.</p>
              </article>
              <article className="step-card">
                <span className="step-number">02</span>
                <div className="step-icon"><span>⌘</span></div>
                <h3>Explore your chart</h3>
                <p>Get acquainted with the language of your chart, from planetary placements to timing cycles.</p>
              </article>
              <article className="step-card">
                <span className="step-number">03</span>
                <div className="step-icon"><span>✧</span></div>
                <h3>Ask what matters</h3>
                <p>Bring your questions to a guided conversation designed to make traditional ideas approachable.</p>
              </article>
            </div>
            <p className="development-note"><span>i</span> Chart calculations and AI interpretations are not available yet. We&apos;ll be clear when they are.</p>
          </div>
        </section>

        <section className="section features-section" id="features">
          <div className="page-container">
            <div className="section-heading-row">
              <SectionHeading
                kicker="Made for discovery"
                title={<>More than a chart.<br /><em>A new perspective.</em></>}
                description="A calm, considered space for exploring the ideas behind your Vedic chart."
              />
              <Link className="text-link section-heading-link" href="/guide">Explore the guide <span aria-hidden="true">↗</span></Link>
            </div>
            <div className="feature-grid">
              {features.map((feature) => (
                <article className="feature-card" key={feature.number}>
                  <span className="feature-number">{feature.number}</span>
                  <span className="feature-icon" aria-hidden="true">{feature.icon}</span>
                  <h3>{feature.title}</h3>
                  <p>{feature.description}</p>
                  <span className="feature-arrow" aria-hidden="true">↗</span>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section life-section" id="life-areas">
          <div className="page-container life-layout">
            <div className="life-intro">
              <span className="section-kicker">Explore what matters</span>
              <h2>Insight for the<br /><em>whole of life.</em></h2>
              <p>Astrology is most useful when it helps you reflect. Choose an area of life to start exploring the questions that matter to you.</p>
              <Link className="text-link" href="/explore">Explore all themes <span aria-hidden="true">↗</span></Link>
            </div>
            <div className="life-list">
              {lifeAreas.map(([number, title, description]) => (
                <Link className="life-row" href="/explore" key={number}>
                  <span className="life-number">{number}</span>
                  <span className="life-copy"><strong>{title}</strong><small>{description}</small></span>
                  <span className="life-arrow" aria-hidden="true">↗</span>
                </Link>
              ))}
            </div>
          </div>
        </section>

        <section className="trust-section">
          <div className="trust-orbit" aria-hidden="true"><span>✦</span></div>
          <div className="page-container trust-content">
            <span className="section-kicker">Tradition with intention</span>
            <h2>Grounded in Jyotisha.<br /><em>Honest about what it can do.</em></h2>
            <p>Vedic astrology offers a symbolic framework for reflection—not a substitute for your own judgment. We aim to honor the tradition, explain our methods, and be transparent about what we know and what we don&apos;t.</p>
            <Link className="button button-outline" href="/guide">Our approach <span aria-hidden="true">↗</span></Link>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
