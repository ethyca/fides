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

export type DropdownCheckboxListProps = {
  /**
   * List of default item values
   */
  defaultValues?: string[];
  /**
   * List of key/value pair items
   */
  items: Map<string, boolean>;
  /**
   * Minimum width of an element
   */
  minWidth?: string;
  /**
   * Event handler invoked when user item selections are applied
   */
  onSelection: (items: Map<string, boolean>) => void;
};

const DropdownCheckboxList: React.FC<DropdownCheckboxListProps> = ({
  defaultValues,
  items,
  minWidth,
  onSelection,
}) => {
  const [pendingItems, setPendingItems] = useState(items);

  // Listeners
  const changeHandler = (values: string[]) => {
    // Copy items
    const temp = new Map(pendingItems);

    // Uncheck all items
    temp.forEach((value, key) => {
      temp.set(key, false);
    });

    // Check the selected items
    values.forEach((v) => {
      temp.set(v, true);
    });

    setPendingItems(temp);
  };
  const clearHandler = () => {
    setPendingItems(items);
    onSelection(new Map<string, boolean>());
  };
  const doneHandler = () => {
    onSelection(pendingItems);
  };

  return (
    <MenuList lineHeight="1rem" minWidth={minWidth} p="0">
      <Flex
        borderBottom="1px"
        borderColor="gray.200"
        cursor="auto"
        p="8px"
        _focus={{
          bg: "none",
        }}
      >
        <Button onClick={clearHandler} size="xs" variant="outline">
          Clear
        </Button>
        <Spacer />
        <Button
          onClick={doneHandler}
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
        onChange={changeHandler}
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

export default DropdownCheckboxList;
