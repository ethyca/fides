import {
  DATA_CATEGORY_COLUMN_ID,
  SYSTEM_DATA_RESPONSIBILITY_TITLE,
  SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME,
} from "~/features/datamap/constants";
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

type Option = {
  value: string | string[];
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
  onCheckboxChange: (fidesKey: string, checked: boolean) => void;
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
  const resetFilters = () => {};
  useGetAllDataUsesQuery();
  const dataUses = useAppSelector(selectDataUses);
  useGetPurposesQuery();
  const purposeResponse= useAppSelector(selectPurposes);

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
      const mappedPurposes = [
        ...Object.entries(purposeResponse.purposes).flatMap((p) => p[1]),
        ...Object.entries(purposeResponse.special_purposes).flatMap((p) => p[1]),
      ];
      console.log(mappedPurposes);

      setPurposeOptions(
        mappedPurposes.map((purpose) => ({
          value: purpose.data_uses,
          displayText: purpose.name,
          isChecked: false,
        }))
      );
    }
  }, [purposeResponse, purposeOptions, setDataUseOptions]);

  const onCheckBoxChange = (
    newValue: string | string[],
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
  const onPurposeChange = (data_uses: string[], checked: boolean) => {
    onCheckBoxChange(data_uses, checked, purposeOptions, setPurposeOptions);
  };

  return {
    isOpen,
    onClose,
    onOpen,
    resetFilters,
    purposeOptions,
    setPurposeOptions,
    dataUseOptions,
    onDataUseChange,
    legalBasisOptions,
    onLegalBasisChange,
  };
};

type Props = {
  isOpen: boolean;
  onClose: () => void;
  resetFilters: () => void;
  dataUseOptions: Option[];
  onDataUseChange: (fidesKey: string, checked: boolean) => void;
  legalBasisOptions: Option[];
  onLegalBasisChange: (legal_basis: string, checked: boolean) => void;
};

export const ConsentManagementFilterModal = ({
  isOpen,
  onClose,
  resetFilters,
  dataUseOptions,
  onDataUseChange,
  legalBasisOptions,
  onLegalBasisChange,
}: Props) => {
  return (
    <FilterModal isOpen={isOpen} onClose={onClose} resetFilters={resetFilters}>
      <FilterSection>
        <AccordionMultifieldFilter
          options={dataUseOptions}
          onCheckboxChange={onDataUseChange}
          header="Data Uses"
        />
        <AccordionMultifieldFilter
          options={legalBasisOptions}
          onCheckboxChange={onLegalBasisChange}
          header="Legal Basis"
        />
      </FilterSection>
    </FilterModal>
  );
};
