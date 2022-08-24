import { Box, Button } from "@fidesui/react";

import DataTabs, { TabData } from "../common/DataTabs";
import {
  useDataCategory,
  useDataQualifier,
  useDataSubject,
  useDataUse,
} from "./hooks";
import { setActiveTaxonomyType } from "./taxonomy.slice";
import TaxonomyTabContent from "./TaxonomyTabContent";
import { TaxonomyTypes } from "./types";

interface TaxonomyTabData extends TabData {
  type: TaxonomyTypes;
}

const TABS: TaxonomyTabData[] = [
  {
    label: "Data Categories",
    content: <TaxonomyTabContent useTaxonomy={useDataCategory} />,
    type: "DataCategory",
  },
  {
    label: "Data Uses",
    content: <TaxonomyTabContent useTaxonomy={useDataUse} />,
    type: "DataUse",
  },
  {
    label: "Data Subjects",
    content: <TaxonomyTabContent useTaxonomy={useDataSubject} />,
    type: "DataSubject",
  },
  {
    label: "Identifiability",
    content: <TaxonomyTabContent useTaxonomy={useDataQualifier} />,
    type: "DataQualifier",
  },
];
const TaxonomyTabs = () => {
  const handleTabChange = (index: number) => {
    setActiveTaxonomyType(TABS[index].type);
  };
  return (
    <Box data-testid="taxonomy-tabs" display="flex">
      <DataTabs isLazy data={TABS} flexGrow={1} onChange={handleTabChange} />
      <Box
        borderBottom="2px solid"
        borderColor="gray.200"
        height="fit-content"
        pr="2"
        pb="2"
      >
        <Button size="sm" variant="outline">
          Add Taxonomy Entity +
        </Button>
      </Box>
    </Box>
  );
};

export default TaxonomyTabs;
