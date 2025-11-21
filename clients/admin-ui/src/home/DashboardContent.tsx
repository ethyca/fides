import { Flex } from "fidesui";
import * as React from "react";

import { HeliosSection } from "./dashboard/sections/HeliosSection";
import { JanusSection } from "./dashboard/sections/JanusSection";
import { LetheSection } from "./dashboard/sections/LetheSection";

/**
 * Main Dashboard Content Component
 * Displays insights across Helios, Janus, and Lethe sections
 */
const DashboardContent = () => (
  <Flex
    direction="column"
    paddingX={10}
    paddingY={6}
    gap={10}
    data-testid="dashboard-content"
  >
    <HeliosSection />
    <JanusSection />
    <LetheSection />
  </Flex>
);

export default DashboardContent;
