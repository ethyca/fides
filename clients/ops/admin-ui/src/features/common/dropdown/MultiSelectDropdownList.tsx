import {
  Button,
  Checkbox,
  CheckboxGroup,
  Flex,
  MenuItem,
  MenuList,
  Spacer,
  Text,
} from "@fidesui/react";
import React, { useState } from "react";

type MultiSelectDropdownListProps = {
  /**
   * List of default item values
   */
  defaultValues?: string[];
  /**
   * List of key/value pair items
   */
  items: Map<string, boolean>;
  /**
   * Event handler invoked when user item selections are applied
   */
  onSelection: (items: Map<string, boolean>) => void;
};

const MultiSelectDropdownList: React.FC<MultiSelectDropdownListProps> = ({
  defaultValues,
  items,
  onSelection,
}) => {
  const [pendingItems, setPendingItems] = useState(items);

  // Listeners
  const handleChange = (values: string[]) => {
    // Copy items
    const temp = new Map(pendingItems);

    // Uncheck all items
    temp.forEach((_value, key) => {
      temp.set(key, false);
    });

    // Check the selected items
    values.forEach((v) => {
      temp.set(v, true);
    });

    setPendingItems(temp);
  };
  const handleClear = () => {
    setPendingItems(items);
    onSelection(new Map<string, boolean>());
  };
  const handleDone = () => {
    onSelection(pendingItems);
  };

  return (
    <MenuList lineHeight="1rem" p="0">
      <Flex
        borderBottom="1px"
        borderColor="gray.200"
        cursor="auto"
        p="8px"
        _focus={{
          bg: "none",
        }}
      >
        <Button onClick={handleClear} size="xs" variant="outline">
          Clear
        </Button>
        <Spacer />
        <Button
          onClick={handleDone}
          size="xs"
          backgroundColor="primary.800"
          color="white"
        >
          Done
        </Button>
      </Flex>
      {/* MenuItems are not rendered unless Menu is open */}
      <CheckboxGroup
        colorScheme="purple"
        defaultValue={defaultValues}
        onChange={handleChange}
      >
        {[...items].sort().map(([key]) => (
          <MenuItem
            key={key}
            paddingTop="10px"
            paddingRight="8.5px"
            paddingBottom="10px"
            paddingLeft="8.5px"
            _focus={{
              bg: "gray.100",
            }}
          >
            <Checkbox
              aria-label={key}
              isChecked={items.get(key)}
              spacing=".5rem"
              value={key}
              width="100%"
            >
              <Text fontSize="0.75rem">{key}</Text>
            </Checkbox>
          </MenuItem>
        ))}
      </CheckboxGroup>
    </MenuList>
  );
};

export default MultiSelectDropdownList;
