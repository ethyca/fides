import {
  Badge,
  Box,
  Button,
  Checkbox,
  CheckboxGroup,
  Flex,
  Spacer,
  VStack,
} from "@fidesui/react";
import { ReactNode } from "react";

const NUM_TO_SHOW = 5;

const PickerCard = <T extends { id: string; name: string }>({
  title,
  items,
  selected,
  onChange,
  toggle,
  onViewMore,
}: {
  title: string;
  items: T[];
  selected: Array<string>;
  onChange: (newSelected: Array<string>) => void;
  toggle?: ReactNode;
  onViewMore: () => void;
}) => {
  const itemsToShow = items.slice(0, NUM_TO_SHOW);
  const numSelected = selected.length;
  const allSelected = items.every((item) => selected.includes(item.id));

  const showViewMore = items.length > NUM_TO_SHOW;

  const handleToggleSelection = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  const handleToggleAll = () => {
    if (allSelected) {
      onChange([]);
    } else {
      onChange(items.map((i) => i.id));
    }
  };

  return (
    <Box
      p={4}
      display="flex"
      alignItems="flex-start"
      gap="4px"
      borderRadius="4px"
      boxShadow="0px 1px 2px 0px rgba(0, 0, 0, 0.06), 0px 1px 3px 0px rgba(0, 0, 0, 0.1)"
      maxWidth="363px"
      fontSize="sm"
      data-testid={`picker-card-${title}`}
    >
      <VStack alignItems="flex-start" spacing={3} width="100%" height="100%">
        <Flex justifyContent="space-between" width="100%">
          <Checkbox
            fontSize="md"
            textTransform="capitalize"
            fontWeight="semibold"
            isChecked={allSelected}
            size="md"
            mr="2"
            onChange={handleToggleAll}
            colorScheme="complimentary"
            data-testid="select-all"
          >
            {title}
          </Checkbox>

          {toggle ?? null}
        </Flex>
        {numSelected > 0 ? (
          <Badge
            colorScheme="purple"
            variant="solid"
            width="fit-content"
            data-testid="num-selected-badge"
          >
            {numSelected} selected
          </Badge>
        ) : null}
        <VStack paddingLeft="6" fontSize="sm" alignItems="start" spacing="2">
          <CheckboxGroup colorScheme="complimentary">
            {itemsToShow.map((location) => (
              <Flex key={location.id} alignItems="center" gap="8px">
                <Checkbox
                  key={location.id}
                  isChecked={selected.includes(location.id)}
                  size="md"
                  fontWeight="500"
                  onChange={() => handleToggleSelection(location.id)}
                  data-testid={`${location.name}-checkbox`}
                >
                  {location.name}
                </Checkbox>
              </Flex>
            ))}
          </CheckboxGroup>
        </VStack>
        <Spacer />
        {showViewMore ? (
          <Button size="xs" variant="ghost" onClick={onViewMore}>
            View more
          </Button>
        ) : null}
      </VStack>
    </Box>
  );
};

export default PickerCard;
