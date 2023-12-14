import { useDisclosure } from "@fidesui/react";
import { useEffect, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  FilterModal,
  FilterSection,
  AccordionMultifieldFilter,
  Option,
} from "~/features/common/modals/FilterModal";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";

import {
  selectDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subject.slice";
import {
  selectDataCategories,
  useGetAllDataCategoriesQuery,
} from "~/features/taxonomy/taxonomy.slice";

export const useDatamapReportFilters = () => {
  const { isOpen, onClose, onOpen } = useDisclosure();
  useGetAllDataUsesQuery();
  const dataUses = useAppSelector(selectDataUses);
  useGetAllDataSubjectsQuery();
  const dataSubjects = useAppSelector(selectDataSubjects);
  useGetAllDataCategoriesQuery();
  const dataCategories = useAppSelector(selectDataCategories);

  const [dataUseOptions, setDataUseOptions] = useState<Option[]>([]);
  const [dataCategoriesOptions, setDataCategoriesOptions] = useState<Option[]>(
    []
  );
  const [dataSubjectOptions, setDataSubjectOptions] = useState<Option[]>([]);

  useEffect(() => {
    if (dataUseOptions.length === 0) {
      setDataUseOptions(
        dataUses.map((dataUse) => ({
          value: dataUse.fides_key,
          displayText: dataUse.name || dataUse.fides_key,
          isChecked: false,
        }))
      );
    }
  }, [dataUses, dataUseOptions, setDataUseOptions]);

  useEffect(() => {
    if (dataCategoriesOptions.length === 0) {
      setDataCategoriesOptions(
        dataCategories.map((dataCategories) => ({
          value: dataCategories.fides_key,
          displayText: dataCategories.name || dataCategories.fides_key,
          isChecked: false,
        }))
      );
    }
  }, [dataCategories, dataCategoriesOptions, setDataCategoriesOptions]);

  useEffect(() => {
    if (dataSubjectOptions.length === 0) {
      setDataSubjectOptions(
        dataSubjects.map((dataSubject) => ({
          value: dataSubject.fides_key,
          displayText: dataSubject.name || dataSubject.fides_key,
          isChecked: false,
        }))
      );
    }
  }, [dataSubjects, dataSubjectOptions, setDataSubjectOptions]);

  const resetFilters = () => {
    setDataUseOptions((prev) => prev.map((o) => ({ ...o, isChecked: false })));
    setDataCategoriesOptions((prev) =>
      prev.map((o) => ({ ...o, isChecked: false }))
    );
    setDataSubjectOptions((prev) =>
      prev.map((o) => ({ ...o, isChecked: false }))
    );
  };

  const onCheckBoxChange = (
    newValue: string,
    checked: boolean,
    options: Option[],
    setOptions: (options: Option[]) => void
  ) => {
    const newOptions = options.map((option) => {
      if (option.value === newValue) {
        return {
          ...option,
          isChecked: checked,
        };
      }
      return option;
    });

    setOptions(newOptions);
  };

  const onDataUseChange = (fidesKey: string, checked: boolean) => {
    onCheckBoxChange(fidesKey, checked, dataUseOptions, setDataUseOptions);
  };

  const onDataCategoriesChange = (fidesKey: string, checked: boolean) => {
    onCheckBoxChange(
      fidesKey,
      checked,
      dataCategoriesOptions,
      setDataCategoriesOptions
    );
  };

  const onDataSubjectChange = (fidesKey: string, checked: boolean) => {
    onCheckBoxChange(
      fidesKey,
      checked,
      dataSubjectOptions,
      setDataSubjectOptions
    );
  };

  return {
    isOpen,
    onClose,
    onOpen,
    resetFilters,
    dataUseOptions,
    onDataUseChange,
    dataCategoriesOptions,
    onDataCategoriesChange,
    dataSubjectOptions,
    onDataSubjectChange,
  };
};

type Props = {
  isOpen: boolean;
  onClose: () => void;
  resetFilters: () => void;
  dataUseOptions: Option[];
  onDataUseChange: (fidesKey: string, checked: boolean) => void;
  dataCategoriesOptions: Option[];
  onDataCategoriesChange: (fidesKey: string, checked: boolean) => void;
  dataSubjectOptions: Option[];
  onDataSubjectChange: (fidesKey: string, checked: boolean) => void;
};

export const DatamapReportFilterModal = ({
  isOpen,
  onClose,
  resetFilters,
  dataUseOptions,
  onDataUseChange,
  dataCategoriesOptions,
  onDataCategoriesChange,
  dataSubjectOptions,
  onDataSubjectChange,
}: Props) => (
  <FilterModal isOpen={isOpen} onClose={onClose} resetFilters={resetFilters}>
    <FilterSection>
      <AccordionMultifieldFilter
        options={dataUseOptions}
        onCheckboxChange={onDataUseChange}
        header="Data uses"
      />
    </FilterSection>
    <FilterSection>
      <AccordionMultifieldFilter
        options={dataCategoriesOptions}
        onCheckboxChange={onDataCategoriesChange}
        header="Data categories"
      />
    </FilterSection>
    <FilterSection>
      <AccordionMultifieldFilter
        options={dataSubjectOptions}
        onCheckboxChange={onDataSubjectChange}
        header="Data subjects"
      />
    </FilterSection>
  </FilterModal>
);
