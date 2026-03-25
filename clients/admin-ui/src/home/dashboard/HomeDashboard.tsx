import type { ReactNode } from "react";

import HomeV1Compact from "./HomeV1Compact";

interface HomeDashboardProps {
  themeToggle?: ReactNode;
}

const HomeDashboard = ({ themeToggle }: HomeDashboardProps) => (
  <div className="px-10 py-6">
    <HomeV1Compact themeToggle={themeToggle} />
  </div>
);

export default HomeDashboard;
