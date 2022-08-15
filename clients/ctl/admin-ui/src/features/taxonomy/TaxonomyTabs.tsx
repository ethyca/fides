import { Box } from "@fidesui/react";

import DataTabs from "../common/DataTabs";
import {
  useDataCategory,
  useDataQualifier,
  useDataSubject,
  useDataUse,
} from "./hooks";
import TaxonomyTabContent from "./TaxonomyTabContent";

const TABS = [
  {
    label: "Data Categories",
    content: <TaxonomyTabContent useTaxonomy={useDataCategory} />,
  },
  {
    label: "Data Uses",
    content: <TaxonomyTabContent useTaxonomy={useDataUse} />,
  },
  {
    label: "Data Subjects",
    content: <TaxonomyTabContent useTaxonomy={useDataSubject} />,
  },
  {
    label: "Identifiability",
    content: <TaxonomyTabContent useTaxonomy={useDataQualifier} />,
  },
];
const TaxonomyTabs = () => (
  <Box data-testid="taxonomy-tabs">
    <DataTabs isLazy data={TABS} />
  </Box>
);

export default TaxonomyTabs;
