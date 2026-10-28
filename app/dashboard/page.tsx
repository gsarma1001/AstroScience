import { DashaTimeline } from "@/components/dasha/dasha-timeline";
import { Footer, Header } from "@/components/site-chrome";

type DashboardPageProps = {
  searchParams: Promise<{ chartId?: string | string[] }>;
};

export default async function DashboardPage({
  searchParams,
}: DashboardPageProps) {
  const params = await searchParams;
  const chartId = Array.isArray(params.chartId)
    ? params.chartId[0] ?? null
    : params.chartId ?? null;

  return (
    <>
      <Header />
      <main className="dashboard-page page-container">
        <div className="dashboard-intro">
          <span className="section-kicker">Your space</span>
          <h1>Your chart, through time.</h1>
          <p>
            Explore traditional planetary periods calculated from a saved birth
            chart.
          </p>
        </div>
        <DashaTimeline chartId={chartId} />
      </main>
      <Footer />
    </>
  );
}
