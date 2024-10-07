import { AntButton as Button, Box } from "fidesui";

import { useAppDispatch } from "~/app/hooks";

import DataTabs, { TabData } from "../common/DataTabs";
import { useDataCategory, useDataSubject, useDataUse } from "./hooks";
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
];
const TaxonomyTabs = () => {
  const dispatch = useAppDispatch();

  const handleAddEntity = () => {
    dispatch(setIsAddFormOpen(true));
  };

  return (
    <Box data-testid="taxonomy-tabs" display="flex">
      <DataTabs border="full-width" data={TABS} flexGrow={1} isLazy />
      <Box
        borderBottom="2px solid"
        borderColor="gray.200"
        height="fit-content"
        pr="2"
        pb="2"
      >
        <Button onClick={handleAddEntity} data-testid="add-taxonomy-btn">
          Add Taxonomy Entity +
        </Button>
      </Box>
    </Box>
  );
};

export default TaxonomyTabs;
