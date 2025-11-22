import { Flex } from "fidesui";
import * as React from "react";

import {
  ConsentCategoriesSection,
  HeliosSection,
  JanusSection,
  LetheSection,
  SummarySection,
} from "./dashboard/sections";

/**
 * Main Dashboard Content Component
 * Displays insights across Summary, Consent Categories, Helios, Janus, and Lethe sections
 */
const DashboardContent = () => (
  <Flex
    direction="column"
    paddingX={10}
    paddingY={6}
    gap={10}
    data-testid="dashboard-content"
  >
    <SummarySection />
    <ConsentCategoriesSection />
    <HeliosSection />
    <JanusSection />
    <LetheSection />
  </Flex>
);

export default DashboardContent;
