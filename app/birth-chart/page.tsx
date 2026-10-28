import { Header, Footer } from "@/components/site-chrome";
import { BirthDetailsForm } from "@/components/birth-details-form";

export const metadata = {
  title: "Birth details — Nakshatra AI",
  description: "Add your birth details to begin exploring your Vedic chart.",
};

export default function BirthChartPage() {
  return (
    <>
      <Header />
      <main className="form-page">
        <div className="page-container form-layout">
          <div className="form-intro">
            <LinkBack />
            <span className="section-kicker">Your story starts here</span>
            <h1>Every chart begins<br />with <em>a moment.</em></h1>
            <p>Your birth details help establish the time and place from which a Vedic chart is traditionally calculated.</p>
            <div className="form-step-list">
              <div className="form-step active"><span>01</span><div><strong>Birth details</strong><small>Tell us when and where</small></div></div>
              <div className="form-step"><span>02</span><div><strong>Your chart</strong><small>Calculation not available yet</small></div></div>
            </div>
            <div className="form-privacy"><span aria-hidden="true">◇</span><p>Your details stay in this browser session only. Saving and chart calculations are not yet available.</p></div>
          </div>
          <BirthDetailsForm />
        </div>
      </main>
      <Footer />
    </>
  );
}

function LinkBack() {
  return <a className="back-link" href="/"><span aria-hidden="true">←</span> Back to home</a>;
}
