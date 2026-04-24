import { useState } from "react";

import ChatPanel from "./ChatPanel";
import DashboardGrid from "./DashboardGrid";

const EntryPointGrid = () => {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100vh",
        background: "#e1e5e6",
        overflow: "hidden",
      }}
    >
      <DashboardGrid expanded={expanded} setExpanded={setExpanded} />
      <ChatPanel expanded={expanded} />
    </div>
  );
};

export default EntryPointGrid;
