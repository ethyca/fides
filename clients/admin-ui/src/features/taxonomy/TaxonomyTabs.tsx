import { Box } from "@fidesui/react";

import DataTabs from "../common/DataTabs";
import DataCategoriesTab from "./DataCategoriesTab";
import DataSubjectsTab from "./DataSubjectsTab";
import DataUsesTab from "./DataUsesTab";
import IdentifiabilityTab from "./IdentifiabilityTab";

const TABS = [
  { label: "Data Categories", content: <DataCategoriesTab /> },
  { label: "Data Uses", content: <DataUsesTab /> },
  { label: "Data Subjects", content: <DataSubjectsTab /> },
  { label: "Identifiability", content: <IdentifiabilityTab /> },
];
const TaxonomyTabs = () => (
  <Box data-testid="taxonomy-tabs">
    <DataTabs isLazy data={TABS} />
  </Box>
);

export default TaxonomyTabs;
