import {
  AntButton as Button,
  AntTag as Tag,
  Box,
  Checkbox,
  CheckboxGroup,
  Flex,
  VStack,
} from "fidesui";
import { ReactNode } from "react";

import { usePicker } from "~/features/common/hooks/usePicker";

export const NUM_TO_SHOW = 5;

export interface CheckboxListProps<T> {
  title: string;
  items: T[];
  selected: Array<string>;
  indeterminate: Array<string>;
  onChange: (newSelected: Array<string>) => void;
  toggle?: ReactNode;
  onViewMore?: () => void;
  numSelected: number;
  variant?: "default" | "emphasize";
}

const PickerCardContainer = ({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) => (
  <Box
    p={4}
    display="flex"
    alignItems="flex-start"
    gap="4px"
    borderRadius="4px"
    boxShadow="0px 1px 2px 0px rgba(0, 0, 0, 0.06), 0px 1px 3px 0px rgba(0, 0, 0, 0.1)"
    fontSize="sm"
    data-testid={`picker-card-${title}`}
  >
    {children}
  </Box>
);

export const PickerCheckboxList = <T extends { id: string; name: string }>({
  title,
  items,
  selected,
  indeterminate,
  onChange,
  toggle,
  onViewMore,
  numSelected,
  variant = "default",
}: CheckboxListProps<T>) => {
  const itemsToShow = onViewMore ? items.slice(0, NUM_TO_SHOW) : items;

  const { allSelected, someSelected, handleToggleAll, handleToggleSelection } =
    usePicker({
      items,
      selected,
      onChange,
    });

  return (
    <VStack alignItems="flex-start" spacing={3} width="100%" height="100%">
      <Flex justifyContent="space-between" width="100%">
        <Checkbox
          fontSize="md"
          textTransform={variant === "emphasize" ? "capitalize" : undefined}
          fontWeight={variant === "emphasize" ? "semibold" : "auto"}
          isChecked={allSelected}
          size="md"
          mr="2"
          onChange={handleToggleAll}
          colorScheme="complimentary"
          data-testid="select-all"
          isIndeterminate={!allSelected && someSelected}
        >
          {title}
        </Checkbox>

        {toggle ?? null}
      </Flex>
      {numSelected > 0 ? (
        <Tag className="w-fit" data-testid="num-selected-badge">
          {numSelected} selected
        </Tag>
      ) : null}
      <VStack paddingLeft="6" fontSize="sm" alignItems="start" spacing="2">
        <CheckboxGroup colorScheme="complimentary">
          {itemsToShow.map((item) => (
            <Flex key={item.id} alignItems="center" gap="8px">
              <Checkbox
                key={item.id}
                isChecked={selected.includes(item.id)}
                isIndeterminate={indeterminate.includes(item.id)}
                size="md"
                fontWeight={variant === "emphasize" ? "500" : "auto"}
                onChange={() => handleToggleSelection(item.id)}
                data-testid={`${item.name}-checkbox`}
              >
                {item.name}
              </Checkbox>
            </Flex>
          ))}
        </CheckboxGroup>
      </VStack>
      {onViewMore ? (
        <Button
          size="small"
          onClick={onViewMore}
          type="text"
          data-testid="view-more-btn"
        >
          View more
        </Button>
      ) : null}
    </VStack>
  );
};

const PickerCard = <T extends { id: string; name: string }>({
  ...props
}: CheckboxListProps<T>) => (
  <PickerCardContainer title={props.title}>
    <PickerCheckboxList {...props} variant="emphasize" />
  </PickerCardContainer>
);

export default PickerCard;
