import { Box, Button } from "@fidesui/react";
import { useState } from "react";

import { useAppDispatch } from "~/app/hooks";

import DataTabs, { TabData } from "../common/DataTabs";
import {
  useDataCategory,
  useDataQualifier,
  useDataSubject,
  useDataUse,
} from "./hooks";
import { setAddTaxonomyType } from "./taxonomy.slice";
import TaxonomyTabContent from "./TaxonomyTabContent";
import { TaxonomyType } from "./types";

interface TaxonomyTabData extends TabData {
  type: TaxonomyType;
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
  const [activeTab, setActiveTab] = useState(0);
  const dispatch = useAppDispatch();

  const handleAddEntity = () => {
    dispatch(setAddTaxonomyType(TABS[activeTab].type));
  };

  return (
    <Box data-testid="taxonomy-tabs" display="flex">
      <DataTabs isLazy data={TABS} flexGrow={1} onChange={setActiveTab} />
      <Box
        borderBottom="2px solid"
        borderColor="gray.200"
        height="fit-content"
        pr="2"
        pb="2"
      >
        <Button size="sm" variant="outline" onClick={handleAddEntity}>
          Add Taxonomy Entity +
        </Button>
      </Box>
    </Box>
  );
};

export default TaxonomyTabs;
