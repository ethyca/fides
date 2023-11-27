import {
  FilterModal,
  FilterSection,
} from "~/features/common/modals/FilterModal";
import {
  Text,
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  Checkbox,
  Heading,
  SimpleGrid,
  useDisclosure,
} from "@fidesui/react";

import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import { useEffect, useState } from "react";
import { useAppSelector } from "~/app/hooks";
import {
  useGetPurposesQuery,
  selectPurposes,
} from "~/features/common/purpose.slice";
import { MappedPurpose } from "~/types/api";

export type FieldValueToIsSelected = {
  [fieldValue: string]: boolean;
};

export type Option = {
  value: string;
  displayText: string;
  isChecked: boolean;
};
type AccordionMultiFieldCheckBoxProps = {
  value: string;
  displayText: string;
  isChecked: boolean;
  onCheckboxChange: (fidesKey: string, checked: boolean) => void;
};

const AccordionMultiFieldCheckBox = ({
  value,
  displayText,
  isChecked,
  onCheckboxChange,
}: AccordionMultiFieldCheckBoxProps) => {
  return (
    <Checkbox
      value={value}
      key={value}
      width="193px"
      height="20px"
      mb="25px"
      isChecked={isChecked}
      onChange={({ target }) => {
        onCheckboxChange(value, (target as HTMLInputElement).checked);
      }}
      _focusWithin={{
        bg: "gray.100",
      }}
      colorScheme="complimentary"
    >
      <Text
        fontSize="sm"
        lineHeight={5}
        height="20px"
        width="170px"
        textOverflow="ellipsis"
        overflow="hidden"
        whiteSpace="nowrap"
      >
        {displayText}
      </Text>
    </Checkbox>
  );
};

type AccordionMultiFieldProps = {
  options: Option[];
  header: string;
  onCheckboxChange: (newValue: string, checked: boolean) => void;
};

const AccordionMultifieldFilter = ({
  options,
  header,
  onCheckboxChange,
}: AccordionMultiFieldProps) => {
  const [isViewingMore, setIsViewingMore] = useState(false);
  const numDefaultOptions = 15;
  const viewableOptions = isViewingMore
    ? options
    : options.slice(0, numDefaultOptions);
  const areExtraOptionsAvailable = options.length > numDefaultOptions;
  console.log(header, onCheckboxChange);

  return (
    <Accordion width="100%" allowToggle>
      <AccordionItem border="0px">
        <Heading height="56px">
          <AccordionButton height="100%">
            <Box
              flex="1"
              alignItems="center"
              justifyContent="center"
              textAlign="left"
            >
              {header}
            </Box>
            <AccordionIcon />
          </AccordionButton>
        </Heading>
        <AccordionPanel>
          <SimpleGrid columns={3}>
            {viewableOptions.map((option) => (
              <AccordionMultiFieldCheckBox
                {...option}
                onCheckboxChange={onCheckboxChange}
              />
            ))}
          </SimpleGrid>
          {!isViewingMore && areExtraOptionsAvailable ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setIsViewingMore(true);
              }}
            >
              View more
            </Button>
          ) : null}
          {isViewingMore && areExtraOptionsAvailable ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setIsViewingMore(false);
              }}
            >
              View less
            </Button>
          ) : null}
        </AccordionPanel>
      </AccordionItem>
    </Accordion>
  );
};

export default AccordionMultifieldFilter;

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
        }))
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
      prev.map((o) => ({ ...o, isChecked: false }))
    );
    setPurposeOptions((prev) => prev.map((o) => ({ ...o, isChecked: false })));
    setConsentCategoryOptions((prev) =>
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
      } else {
        return option;
      }
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
      setLegalBasisOptions
    );
  };
  const onPurposeChange = (dataUses: string, checked: boolean) => {
    onCheckBoxChange(dataUses, checked, purposeOptions, setPurposeOptions);
  };
  const onConsentCategoryChange = (
    consentCategory: string,
    checked: boolean
  ) => {
    onCheckBoxChange(
      consentCategory,
      checked,
      consentCategoryOptions,
      setConsentCategoryOptions
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
}: Props) => {
  return (
    <FilterModal isOpen={isOpen} onClose={onClose} resetFilters={resetFilters}>
      <FilterSection>
        {isTcfEnabled ? (
          <AccordionMultifieldFilter
            options={purposeOptions}
            onCheckboxChange={onPurposeChange}
            header="TCF purposes"
          />
        ) : null}
        <AccordionMultifieldFilter
          options={dataUseOptions}
          onCheckboxChange={onDataUseChange}
          header="Data Uses"
        />

        {isTcfEnabled ? (
          <AccordionMultifieldFilter
            options={legalBasisOptions}
            onCheckboxChange={onLegalBasisChange}
            header="Legal Basis"
          />
        ) : null}
        {!isTcfEnabled ? (
          <AccordionMultifieldFilter
            options={consentCategoryOptions}
            onCheckboxChange={onConsentCategoryChange}
            header="Consent Categories"
          />
        ) : null}
      </FilterSection>
    </FilterModal>
  );
};
