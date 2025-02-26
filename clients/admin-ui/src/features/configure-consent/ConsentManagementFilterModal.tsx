import { Accordion, useDisclosure } from "fidesui";
import { useEffect, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  AccordionMultifieldFilter,
  FilterModal,
  FilterSection,
  Option,
} from "~/features/common/modals/FilterModal";
import {
  selectPurposes,
  useGetPurposesQuery,
} from "~/features/common/purpose.slice";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";

export const useConsentManagementFilters = () => {
  const { isOpen, onClose, onOpen } = useDisclosure();
  useGetAllDataUsesQuery();
  const dataUses = useAppSelector(selectDataUses);
  useGetPurposesQuery();
  const purposeResponse = useAppSelector(selectPurposes);

  const [purposeOptions, setPurposeOptions] = useState<Option[]>([]);
  const [dataUseOptions, setDataUseOptions] = useState<Option[]>([]);
  const [legalBasisOptions, setLegalBasisOptions] = useState<Option[]>([
    {
      displayText: "Consent",
      value: "Consent",
      isChecked: false,
    },
    {
      displayText: "Legitimate Interest",
      value: "Legitimate interests",
      isChecked: false,
    },
  ]);
  const [consentCategoryOptions, setConsentCategoryOptions] = useState<
    Option[]
  >([
    {
      displayText: "Advertising",
      value: "advertising",
      isChecked: false,
    },
    {
      displayText: "Analytics",
      value: "analytics",
      isChecked: false,
    },
    {
      displayText: "Functional",
      value: "functional",
      isChecked: false,
    },
    {
      displayText: "Essential",
      value: "essential",
      isChecked: false,
    },
  ]);

  useEffect(() => {
    if (dataUseOptions.length === 0) {
      setDataUseOptions(
        dataUses.map((dataUse) => ({
          value: dataUse.fides_key,
          displayText: dataUse.name || dataUse.fides_key,
          isChecked: false,
        })),
      );
    }
  }, [dataUses, dataUseOptions, setDataUseOptions]);
  useEffect(() => {
    if (purposeOptions.length === 0) {
      setPurposeOptions([
        ...Object.entries(purposeResponse.purposes).map((p) => ({
          value: `normal.${p[0]}`,
          displayText: p[1].name,
          isChecked: false,
        })),
        ...Object.entries(purposeResponse.special_purposes).map((p) => ({
          value: `special.${p[0]}`,
          displayText: p[1].name,
          isChecked: false,
        })),
      ]);
    }
  }, [purposeResponse, purposeOptions, setDataUseOptions]);

  const resetFilters = () => {
    setDataUseOptions((prev) => prev.map((o) => ({ ...o, isChecked: false })));
    setLegalBasisOptions((prev) =>
      prev.map((o) => ({ ...o, isChecked: false })),
    );
    setPurposeOptions((prev) => prev.map((o) => ({ ...o, isChecked: false })));
    setConsentCategoryOptions((prev) =>
      prev.map((o) => ({ ...o, isChecked: false })),
    );
  };

  const onCheckBoxChange = (
    newValue: string,
    checked: boolean,
    options: Option[],
    setOptions: (options: Option[]) => void,
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

  const onLegalBasisChange = (legalBasis: string, checked: boolean) => {
    onCheckBoxChange(
      legalBasis,
      checked,
      legalBasisOptions,
      setLegalBasisOptions,
    );
  };
  const onPurposeChange = (purposes: string, checked: boolean) => {
    onCheckBoxChange(purposes, checked, purposeOptions, setPurposeOptions);
  };
  const onConsentCategoryChange = (
    consentCategory: string,
    checked: boolean,
  ) => {
    onCheckBoxChange(
      consentCategory,
      checked,
      consentCategoryOptions,
      setConsentCategoryOptions,
    );
  };

  return {
    isOpen,
    onClose,
    onOpen,
    resetFilters,
    purposeOptions,
    onPurposeChange,
    dataUseOptions,
    onDataUseChange,
    legalBasisOptions,
    onLegalBasisChange,
    consentCategoryOptions,
    onConsentCategoryChange,
  };
};

type Props = {
  isOpen: boolean;
  isTcfEnabled: boolean;
  onClose: () => void;
  resetFilters: () => void;
  purposeOptions: Option[];
  onPurposeChange: (data_uses: string, checked: boolean) => void;
  dataUseOptions: Option[];
  onDataUseChange: (fidesKey: string, checked: boolean) => void;
  legalBasisOptions: Option[];
  onLegalBasisChange: (legaBasis: string, checked: boolean) => void;
  consentCategoryOptions: Option[];
  onConsentCategoryChange: (consentCategory: string, checked: boolean) => void;
};

export const ConsentManagementFilterModal = ({
  isOpen,
  isTcfEnabled,
  onClose,
  resetFilters,
  purposeOptions,
  onPurposeChange,
  dataUseOptions,
  onDataUseChange,
  legalBasisOptions,
  onLegalBasisChange,
  consentCategoryOptions,
  onConsentCategoryChange,
}: Props) => (
  <FilterModal isOpen={isOpen} onClose={onClose} resetFilters={resetFilters}>
    <Accordion>
      <FilterSection>
        {isTcfEnabled ? (
          <AccordionMultifieldFilter
            options={purposeOptions}
            onCheckboxChange={onPurposeChange}
            header="TCF purposes"
            columns={1}
            numDefaultOptions={5}
          />
        ) : null}
        <AccordionMultifieldFilter
          options={dataUseOptions}
          onCheckboxChange={onDataUseChange}
          header="Data uses"
        />

        {isTcfEnabled ? (
          <AccordionMultifieldFilter
            options={legalBasisOptions}
            onCheckboxChange={onLegalBasisChange}
            header="Legal basis"
          />
        ) : null}
        {!isTcfEnabled ? (
          <AccordionMultifieldFilter
            options={consentCategoryOptions}
            onCheckboxChange={onConsentCategoryChange}
            header="Consent categories"
          />
        ) : null}
      </FilterSection>
    </Accordion>
  </FilterModal>
);
