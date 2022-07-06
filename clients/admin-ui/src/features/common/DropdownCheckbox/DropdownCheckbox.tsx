import { PlacementWithLogical } from "@chakra-ui/react";
import { Button, Grid, Menu, MenuButton, Text, Tooltip } from "@fidesui/react";
import React, { useState } from "react";

import { ArrowDownLineIcon } from "../Icon";
import DropdownCheckboxList from "./DropdownCheckboxList";

export type DropdownCheckboxProps = {
  /**
   * Boolean to determine if the dropdown is to be immediately close on a user selection
   */
  closeOnSelect?: boolean;
  /**
   * List of key/value pairs to be rendered as a checkbox list
   */
  list: Map<string, boolean>;
  /**
   * Minimum width of an element
   */
  minWidth?: string;
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
  title: string;
  /**
   * Position of the tooltip
   */
  tooltipPlacement?: PlacementWithLogical;
};

const DropdownCheckbox: React.FC<DropdownCheckboxProps> = ({
  closeOnSelect = false,
  list,
  minWidth,
  onChange,
  selectedList,
  title,
  tooltipPlacement = "auto",
}) => {
  const defaultItems = new Map(list);

  // Hooks
  const [isOpen, setIsOpen] = useState(false);

  // Listeners
  const selectionHandler = (items: Map<string, boolean>) => {
    const temp = new Map([...items].filter(([, v]) => v === true));
    onChange([...temp.keys()]);
    setIsOpen(false);
  };
  const openHandler = () => {
    setIsOpen(true);
  };

  const selectedItemsText =
    selectedList.size > 0 ? [...selectedList.keys()].sort().join(", ") : title;

  return (
    <Grid>
      <Menu
        closeOnSelect={closeOnSelect}
        isLazy
        onClose={() => setIsOpen(false)}
        onOpen={openHandler}
      >
        <Tooltip
          fontSize=".75rem"
          hasArrow
          aria-label=""
          label={selectedItemsText}
          lineHeight="1.25rem"
          isDisabled={!(selectedList.size > 0)}
          placement={tooltipPlacement}
        >
          <MenuButton
            aria-label={title}
            as={Button}
            fontWeight="normal"
            minWidth={minWidth}
            rightIcon={<ArrowDownLineIcon />}
            size="sm"
            variant="outline"
            _active={{
              bg: "none",
            }}
            _hover={{
              bg: "none",
            }}
          >
            <Text isTruncated>{selectedItemsText}</Text>
          </MenuButton>
        </Tooltip>
        {isOpen ? (
          <DropdownCheckboxList
            defaultValues={[...selectedList.keys()]}
            items={defaultItems}
            minWidth={minWidth}
            onSelection={selectionHandler}
          />
        ) : null}
      </Menu>
    </Grid>
  );
};

export default DropdownCheckbox;
