import { Flex } from "fidesui";
import * as React from "react";

import {
  ConsentCategoriesSection,
  DataClassificationSection,
  HeliosSection,
  JanusSection,
  LetheSection,
  SummarySection,
} from "./dashboard/sections";

/**
 * Main Dashboard Content Component
 * Displays insights across Summary, Consent Categories, Data Classification, Helios, Janus, and Lethe sections
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
    <DataClassificationSection />
  </Flex>
);

export default DashboardContent;
