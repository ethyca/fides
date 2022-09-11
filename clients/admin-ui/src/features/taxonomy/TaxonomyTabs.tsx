import { Box, Button } from "@fidesui/react";

import { useAppDispatch } from "~/app/hooks";

import DataTabs, { TabData } from "common/DataTabs";
import {
  useDataCategory,
  useDataQualifier,
  useDataSubject,
  useDataUse,
} from "./hooks";
import { setIsAddFormOpen } from "./taxonomy.slice";
import TaxonomyTabContent from "./TaxonomyTabContent";

const TABS: TabData[] = [
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
const TaxonomyTabs = () => {
  const dispatch = useAppDispatch();

  const handleAddEntity = () => {
    dispatch(setIsAddFormOpen(true));
  };

  return (
    <Box data-testid="taxonomy-tabs" display="flex">
      <DataTabs isLazy data={TABS} flexGrow={1} />
      <Box
        borderBottom="2px solid"
        borderColor="gray.200"
        height="fit-content"
        pr="2"
        pb="2"
      >
        <Button
          size="sm"
          variant="outline"
          onClick={handleAddEntity}
          data-testid="add-taxonomy-btn"
        >
          Add Taxonomy Entity +
        </Button>
      </Box>
    </Box>
  );
};

export default TaxonomyTabs;
