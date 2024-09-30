import {
  AntButton,
  Box,
  Checkbox,
  CheckboxGroup,
  Flex,
  MenuItem,
  MenuList,
  Spacer,
} from "fidesui";
import React, { useState } from "react";

type MultiSelectDropdownListProps = {
  defaultValues?: string[];
  items: Map<string, boolean>;
  onSelection: (items: Map<string, boolean>) => void;
};

/**
 * @param defaultValues - List of default item values
 * @param items - List of key/value pair items
 * @param onSelection - Event handler invoked when user item selections are applied
 */
const MultiSelectDropdownList = ({
  defaultValues,
  items,
  onSelection,
}: MultiSelectDropdownListProps) => {
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
    <MenuList lineHeight="1rem" pt="0">
      <Flex borderBottom="1px" borderColor="gray.200" cursor="auto" p="8px">
        <AntButton onClick={handleClear} size="small">
          Clear
        </AntButton>
        <Spacer />
        <AntButton type="primary" onClick={handleDone} size="small">
          Done
        </AntButton>
      </Flex>
      {/* MenuItems are not rendered unless Menu is open */}
      <Box maxH="360px" overflow="auto">
        <CheckboxGroup
          colorScheme="purple"
          defaultValue={defaultValues}
          onChange={handleChange}
        >
          {[...items].sort().map(([key]) => (
            <MenuItem
              key={key}
              p={0}
              onKeyPress={(e) => {
                if (e.key === " ") {
                  e.currentTarget.getElementsByTagName("input")[0].click();
                }
                if (e.key === "Enter") {
                  handleDone();
                }
              }}
            >
              <Checkbox
                isChecked={items.get(key)}
                spacing={2}
                value={key}
                width="100%"
                fontSize="0.75rem"
                paddingTop="10px"
                paddingRight="8.5px"
                paddingBottom="10px"
                paddingLeft="8.5px"
                onClick={(e) => e.stopPropagation()}
              >
                {key}
              </Checkbox>
            </MenuItem>
          ))}
        </CheckboxGroup>
      </Box>
    </MenuList>
  );
};

export default MultiSelectDropdownList;
