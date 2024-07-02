import { Badge, Checkbox, CheckboxGroup, Flex } from "fidesui";

const MonitorDatabasePicker = ({
  items,
  itemCount,
  selected,
  allSelected,
  someSelected,
  handleToggleSelection,
  handleToggleAll,
}: {
  items: { name: string; id: string }[];
  itemCount: number;
  selected: string[];
  allSelected: boolean;
  someSelected: boolean;
  handleToggleSelection: (item: string) => void;
  handleToggleAll: () => void;
}) => {
  const numSelected = allSelected ? itemCount : selected.length;

  return (
    <Flex w="full" direction="column" gap={3}>
      <Checkbox
        fontSize="md"
        isChecked={allSelected}
        size="md"
        mr={2}
        onChange={handleToggleAll}
        colorScheme="complimentary"
        data-testid="select-all"
        isIndeterminate={!allSelected && someSelected}
      >
        Select all
      </Checkbox>
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
      <Flex pl={6} fontSize="sm" gap={2} direction="column">
        <CheckboxGroup colorScheme="complimentary">
          {items.map((item) => (
            <Checkbox
              key={item.id}
              isChecked={selected.includes(item.id) || allSelected}
              size="md"
              onChange={() => handleToggleSelection(item.id)}
              disabled={allSelected}
            >
              {item.name}
            </Checkbox>
          ))}
        </CheckboxGroup>
      </Flex>
    </Flex>
  );
};

export default MonitorDatabasePicker;
