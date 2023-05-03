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
} from "@fidesui/react";
import { useState } from "react";
import { ColumnInstance } from "react-table";

import { useAppSelector } from "~/app/hooks";
import { DatamapRow } from "~/features/datamap";
import { DATA_CATEGORY_COLUMN_ID } from "~/features/datamap/constants";
import { selectDataCategoriesMap } from "~/features/taxonomy";

import { useAccordionMultifieldFilter } from "./helpers";

export type FieldValueToIsSelected = {
  [fieldValue: string]: boolean;
};

type AccordionMultiFieldCheckBoxProps = {
  option: string;
  columnId: string;
  filterValue: FieldValueToIsSelected;
  toggleFilterOption: (
    option: keyof FieldValueToIsSelected,
    isSelected: boolean
  ) => void;
};

const AccordionMultiFieldCheckBox = ({
  option,
  columnId,
  filterValue,
  toggleFilterOption,
}: AccordionMultiFieldCheckBoxProps) => {
  const categoriesMap = useAppSelector(selectDataCategoriesMap);
  const displayText =
    columnId === DATA_CATEGORY_COLUMN_ID
      ? categoriesMap.get(option)?.name ?? option
      : option;
  return (
    <Checkbox
      value={option}
      key={option}
      width="193px"
      height="20px"
      mb="25px"
      isChecked={filterValue[option] ?? false}
      onChange={({ target }) => {
        toggleFilterOption(option, (target as HTMLInputElement).checked);
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

interface AccordionMultiFieldProps {
  column: ColumnInstance<DatamapRow> & {
    filterValue?: FieldValueToIsSelected | undefined;
    rows: DatamapRow[];
  };
}

export type ClearFilterRef = { clearFilter(): void };

const AccordionMultifieldFilter = ({ column }: AccordionMultiFieldProps) => {
  const { filterValue, toggleFilterOption, options } =
    useAccordionMultifieldFilter(column);

  const [isViewingMore, setIsViewingMore] = useState(false);
  const numDefaultOptions = 15;
  const viewableOptions = isViewingMore
    ? options
    : options.slice(0, numDefaultOptions);
  const areExtraOptionsAvailable = options.length > numDefaultOptions;

  return (
    <Accordion width="100%" allowToggle key={column.id}>
      <AccordionItem border="0px">
        <Heading height="56px">
          <AccordionButton height="100%">
            <Box
              flex="1"
              alignItems="center"
              justifyContent="center"
              textAlign="left"
            >
              {column.Header}
            </Box>
            <AccordionIcon />
          </AccordionButton>
        </Heading>
        <AccordionPanel>
          <SimpleGrid columns={3}>
            {viewableOptions.map((option) => (
              <AccordionMultiFieldCheckBox
                key={option}
                columnId={column.id}
                option={option}
                filterValue={filterValue}
                toggleFilterOption={toggleFilterOption}
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
