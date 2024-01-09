import {
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
  Text,
  useDisclosure,
} from "@fidesui/react";
import { useEffect, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  FilterModal,
  FilterSection,
} from "~/features/common/modals/FilterModal";
import {
  selectPurposes,
  useGetPurposesQuery,
} from "~/features/common/purpose.slice";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";

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
}: AccordionMultiFieldCheckBoxProps) => (
  <Checkbox
    value={value}
    key={value}
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
      textOverflow="ellipsis"
      overflow="hidden"
    >
      {displayText}
    </Text>
  </Checkbox>
);

type AccordionMultiFieldProps = {
  options: Option[];
  header: string;
  onCheckboxChange: (newValue: string, checked: boolean) => void;
  columns?: number;
  numDefaultOptions?: number;
};

const AccordionMultifieldFilter = ({
  options,
  header,
  onCheckboxChange,
  columns = 3,
  numDefaultOptions = 15,
}: AccordionMultiFieldProps) => {
  const [isViewingMore, setIsViewingMore] = useState(false);
  const viewableOptions = isViewingMore
    ? options
    : options.slice(0, numDefaultOptions);
  const areExtraOptionsAvailable = options.length > numDefaultOptions;

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
              fontWeight={600}
            >
              {header}
            </Box>
            <AccordionIcon />
          </AccordionButton>
        </Heading>
        <AccordionPanel>
          <SimpleGrid columns={columns}>
            {viewableOptions.map((option) => (
              <AccordionMultiFieldCheckBox
                key={option.value}
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
    if (purposeResponse && purposeOptions.length === 0) {
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
      setLegalBasisOptions
    );
  };
  const onPurposeChange = (purposes: string, checked: boolean) => {
    onCheckBoxChange(purposes, checked, purposeOptions, setPurposeOptions);
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
}: Props) => (
  <FilterModal isOpen={isOpen} onClose={onClose} resetFilters={resetFilters}>
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
  </FilterModal>
);
