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
import { useAppSelector } from "~/app/hooks";
import { useEffect, useState } from "react";

export type FieldValueToIsSelected = {
  [fieldValue: string]: boolean;
};

type Option = { value: string; displayText: string; isChecked: boolean };
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

  const [dataUseOptions, setDataUseOptions] = useState<Option[]>([]);

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
  const onCheckboxChange = (fidesKey: string, checked: boolean) => {
    const newOptions = dataUseOptions.map((option) => {
      if (option.value === fidesKey) {
        return {
          ...option,
          isChecked: checked,
        };
      } else {
        return option;
      }
    });

    setDataUseOptions(newOptions);

    // dataUseOptions.sort((a, b)=> a.displayText.localeCompare(b.displayText))
  };

  return {
    isOpen,
    onClose,
    onOpen,
    resetFilters,
    dataUseOptions,
    onCheckboxChange,
  };
};

type Props = {
  dataUseOptions: Option[];
  isOpen: boolean;
  onClose: () => void;
  resetFilters: () => void;
  onCheckboxChange: (fidesKey: string, checked: boolean) => void;
};

export const ConsentManagementFilterModal = ({
  isOpen,
  onClose,
  resetFilters,
  dataUseOptions,
  onCheckboxChange,
}: Props) => {
  return (
    <FilterModal isOpen={isOpen} onClose={onClose} resetFilters={resetFilters}>
      <FilterSection>
        <AccordionMultifieldFilter
          options={dataUseOptions}
          onCheckboxChange={onCheckboxChange}
          header="Data Uses"
        />
      </FilterSection>
    </FilterModal>
  );
};
