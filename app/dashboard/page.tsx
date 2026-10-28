import { Footer, Header } from "@/components/site-chrome";
import { ComingSoon } from "@/components/coming-soon";

export default function DashboardPage() {
  return <><Header /><ComingSoon kicker="Your space" title="A place for your journey." description="Your dashboard will bring your chart and saved reflections together. No personal data or chart details are stored yet." /><Footer /></>;
}
