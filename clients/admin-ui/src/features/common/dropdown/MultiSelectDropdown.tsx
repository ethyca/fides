import {
  AntButton as Button,
  ArrowDownLineIcon,
  Box,
  HStack,
  Menu,
  MenuButton,
  PlacementWithLogical,
  Text,
  Tooltip,
} from "fidesui";
import React, { useState } from "react";

import MultiSelectDropdownList from "./MultiSelectDropdownList";

type MultiSelectDropdwonProps = {
  /**
   * Boolean to determine if the dropdown is to be immediately close on a user selection
   */
  closeOnSelect?: boolean;
  /**
   * List of key/value pairs to be rendered as a checkbox list
   */
  list: Map<string, boolean>;
  /**
   * Parent callback event handler invoked when list of selection values have changed
   */
  onChange: (values: string[]) => void;
  /**
   * List of key/value pairs which are marked for selection
   */
  selectedList: Map<string, boolean>;
  /**
   * Placeholder
   */
  label: string;
  /**
   * Disable showing a tooltip
   */
  tooltipDisabled?: boolean;
  /**
   * Position of the tooltip
   */
  tooltipPlacement?: PlacementWithLogical;
  /**
   * Fixed Width of the textbox within the Menu Button component
   */
  width?: string;
};

const MultiSelectDropdown = ({
  closeOnSelect = false,
  list,
  onChange,
  selectedList,
  label,
  tooltipDisabled = false,
  tooltipPlacement = "auto",
  width,
}: MultiSelectDropdwonProps) => {
  const defaultItems = new Map(list);

  // Hooks
  const [isOpen, setIsOpen] = useState(false);

  // Listeners
  const handleClose = () => {
    setIsOpen(false);
  };
  const handleOpen = () => {
    setIsOpen(true);
  };
  const handleSelection = (items: Map<string, boolean>) => {
    const temp = new Map([...items].filter(([, v]) => v === true));
    onChange([...temp.keys()]);
    handleClose();
  };

  const getMenuButtonText = () => {
    if (!tooltipDisabled) {
      return selectedList.size > 0
        ? [...selectedList.keys()].sort().join(", ")
        : label;
    }
    return label;
  };

  return (
    <Box>
      <Menu
        closeOnSelect={closeOnSelect}
        isLazy
        onClose={handleClose}
        onOpen={handleOpen}
        strategy="fixed"
      >
        {({ onClose }) => (
          <>
            <Tooltip
              fontSize=".75rem"
              hasArrow
              aria-label=""
              label={getMenuButtonText()}
              lineHeight="1.25rem"
              isDisabled={tooltipDisabled || !(selectedList.size > 0)}
              placement={tooltipPlacement}
            >
              <MenuButton
                aria-label={getMenuButtonText()}
                as={Button}
                icon={<ArrowDownLineIcon />}
                iconPosition="end"
                className="hover:bg-none active:bg-none"
              >
                {!tooltipDisabled && (
                  <Text
                    display="inline-block"
                    noOfLines={1}
                    wordBreak="break-all"
                    width={width}
                  >
                    {getMenuButtonText()}
                  </Text>
                )}
                {tooltipDisabled && (
                  <HStack>
                    <Text>{getMenuButtonText()}</Text>
                    {selectedList.size > 0 && (
                      <Text color="complimentary.500">{selectedList.size}</Text>
                    )}
                  </HStack>
                )}
              </MenuButton>
            </Tooltip>
            {isOpen && (
              <MultiSelectDropdownList
                defaultValues={[...selectedList.keys()]}
                items={defaultItems}
                onSelection={(items) => {
                  handleSelection(items);
                  onClose();
                }}
              />
            )}
          </>
        )}
      </Menu>
    </Box>
  );
};

export default MultiSelectDropdown;
