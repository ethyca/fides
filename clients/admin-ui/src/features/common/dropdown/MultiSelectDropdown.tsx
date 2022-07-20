import { PlacementWithLogical } from "@chakra-ui/react";
import {
  Box,
  Button,
  HStack,
  Menu,
  MenuButton,
  Text,
  Tooltip,
} from "@fidesui/react";
import React, { useState } from "react";

import { ArrowDownLineIcon } from "../Icon";
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

const MultiSelectDropdown: React.FC<MultiSelectDropdwonProps> = ({
  closeOnSelect = false,
  list,
  onChange,
  selectedList,
  label,
  tooltipDisabled = false,
  tooltipPlacement = "auto",
  width,
}) => {
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
      >
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
            fontWeight="normal"
            rightIcon={<ArrowDownLineIcon />}
            size="sm"
            variant="outline"
            _active={{
              bg: "none",
            }}
            _focus={{
              bg: "none",
            }}
            _hover={{
              bg: "none",
            }}
          >
            {!tooltipDisabled && (
              <Text display="inline-block" isTruncated width={width}>
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
        {isOpen ? (
          <MultiSelectDropdownList
            defaultValues={[...selectedList.keys()]}
            items={defaultItems}
            onSelection={handleSelection}
          />
        ) : null}
      </Menu>
    </Box>
  );
};

export default MultiSelectDropdown;
