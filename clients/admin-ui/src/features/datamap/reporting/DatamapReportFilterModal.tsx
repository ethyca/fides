import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionItemProps,
  AccordionPanel,
  Box,
  Heading,
} from "fidesui";
import { useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import CheckboxTree from "~/features/common/CheckboxTree";
import StandardDialog, {
  StandardDialogProps,
} from "~/features/common/modals/StandardDialog";
import { TreeNode } from "~/features/common/types";
import {
  selectDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subject.slice";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import { transformTaxonomyEntityToNodes } from "~/features/taxonomy/helpers";
import {
  selectDataCategories,
  useGetAllDataCategoriesQuery,
} from "~/features/taxonomy/taxonomy.slice";

import { DatamapReportFilterSelections } from "../types";

interface DatamapReportFilterModalProps
  extends Omit<StandardDialogProps, "children" | "onConfirm"> {
  selectedFilters: DatamapReportFilterSelections;
  onFilterChange: (selectedFilters: DatamapReportFilterSelections) => void;
}

interface FilterModalAccordionItemProps extends AccordionItemProps {
  label: string;
  children: React.ReactNode;
}
const FilterModalAccordionItem = ({
  label,
  children,
  ...props
}: FilterModalAccordionItemProps) => (
  <AccordionItem {...props}>
    <Heading>
      <AccordionButton
        height="100%"
        data-testid="filter-modal-accordion-button"
        textAlign="left"
        fontWeight={600}
      >
        <Box flex={1}>{label}</Box>
        <AccordionIcon boxSize={7} />
      </AccordionButton>
    </Heading>
    <AccordionPanel>{children}</AccordionPanel>
  </AccordionItem>
);

export const DatamapReportFilterModal = ({
  selectedFilters,
  onFilterChange,
  onClose,
  ...props
}: DatamapReportFilterModalProps): JSX.Element => {
  useGetAllDataUsesQuery();
  useGetAllDataSubjectsQuery();
  useGetAllDataCategoriesQuery();

  const {
    dataUses: selectedDataUses,
    dataSubjects: selectedDataSubjects,
    dataCategories: selectedDataCategories,
  } = selectedFilters;

  const dataUses = useAppSelector(selectDataUses);
  const dataSubjects = useAppSelector(selectDataSubjects);
  const dataCategories = useAppSelector(selectDataCategories);

  const [checkedUses, setCheckedUses] = useState<string[]>(selectedDataUses);
  const [checkedSubjects, setCheckedSubjects] =
    useState<string[]>(selectedDataSubjects);
  const [checkedCategories, setCheckedCategories] = useState<string[]>(
    selectedDataCategories,
  );

  const dataUseNodes: TreeNode[] = useMemo(
    () => transformTaxonomyEntityToNodes(dataUses),
    [dataUses],
  );
  const dataSubjectNodes: TreeNode[] = useMemo(
    () => transformTaxonomyEntityToNodes(dataSubjects),
    [dataSubjects],
  );
  const dataCategoryNodes: TreeNode[] = useMemo(
    () => transformTaxonomyEntityToNodes(dataCategories),
    [dataCategories],
  );

  const resetFilters = () => {
    setCheckedUses([]);
    setCheckedSubjects([]);
    setCheckedCategories([]);
    onFilterChange({
      dataUses: [],
      dataSubjects: [],
      dataCategories: [],
    });
    onClose();
  };

  const handleFilterChange = () => {
    onFilterChange({
      dataUses: checkedUses,
      dataSubjects: checkedSubjects,
      dataCategories: checkedCategories,
    });
    onClose();
  };
  return (
    <StandardDialog
      heading="Filter Datamap Report"
      {...props}
      onCancel={resetFilters}
      onConfirm={handleFilterChange}
      onClose={onClose}
      cancelButtonText="Reset filters"
      continueButtonText="Done"
      data-testid="datamap-report-filter-modal"
    >
      <Accordion allowToggle>
        <FilterModalAccordionItem label="Data uses">
          <CheckboxTree
            nodes={dataUseNodes}
            selected={checkedUses}
            onSelected={setCheckedUses}
            data-testid="filter-modal-checkbox-tree-uses"
          />
        </FilterModalAccordionItem>
        <FilterModalAccordionItem label="Data categories">
          <CheckboxTree
            nodes={dataCategoryNodes}
            selected={checkedCategories}
            onSelected={setCheckedCategories}
            data-testid="filter-modal-checkbox-tree-categories"
          />
        </FilterModalAccordionItem>
        <FilterModalAccordionItem label="Data subjects">
          <CheckboxTree
            nodes={dataSubjectNodes}
            selected={checkedSubjects}
            onSelected={setCheckedSubjects}
            data-testid="filter-modal-checkbox-tree-subjects"
          />
        </FilterModalAccordionItem>
      </Accordion>
    </StandardDialog>
  );
};
