import {
  ArrowDownLineIcon,
  Box,
  Button,
  Menu,
  MenuButton,
  MenuButtonProps,
  Tag,
  TagCloseButton,
  TagLabel,
} from "fidesui";
import { useState } from "react";

import MultiSelectDropdownList from "./MultiSelectDropdownList";

interface MultiSelectTagsProps extends Omit<MenuButtonProps, "onChange"> {
  closeOnSelect?: boolean;
  list: Map<string, boolean>;
  selectedList: Map<string, boolean>;
  placeholder?: string;
  onChange: (values: string[]) => void;
}

/**
 * Dropdown menu with a list of checkboxes for multiple selection that displays the selected values in a textbox as chips
 * @param closeOnSelect - Boolean to determine if the dropdown is to be immediately close on a user selection
 * @param list - List of key/value pairs to be rendered as a checkbox list
 * @param onChange - Parent callback event handler invoked when list of selection values have changed
 * @param selectedList - List of key/value pairs which are marked for selection
 * @param placeholder - Placeholder text to be displayed when no items are selected
 */
export const MultiSelectTags = ({
  closeOnSelect = false,
  list,
  onChange,
  selectedList,
  placeholder = "Select one or more items",
  ...props
}: MultiSelectTagsProps) => {
  const defaultItems = new Map(list);
  const [isOpen, setIsOpen] = useState(false);

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

  const handleRemoveItem = (key: string) => {
    const temp = new Map(selectedList);
    temp.delete(key);
    onChange([...temp.keys()]);
  };

  return (
    <Menu
      isLazy
      closeOnSelect={closeOnSelect}
      onClose={handleClose}
      onOpen={handleOpen}
    >
      {({ onClose }) => (
        <>
          <Box
            sx={{
              border: "1px solid",
              borderColor: "gray.200",
              borderRadius: "md",
              display: "flex",
              flexWrap: "wrap",
              gap: 2,
              py: 2,
              pl: 2,
              pr: 10,
              position: "relative",
              ...props.sx,
            }}
          >
            {selectedList.size > 0
              ? [...selectedList.keys()].map((key) => (
                  <Tag key={key} size="md" zIndex={1}>
                    <TagLabel>{key}</TagLabel>
                    <TagCloseButton onClick={() => handleRemoveItem(key)} />
                  </Tag>
                ))
              : placeholder}
            <MenuButton
              as={Button}
              rightIcon={<ArrowDownLineIcon />}
              variant="ghost"
              _active={{
                bg: "none",
              }}
              _hover={{
                bg: "none",
              }}
              aria-label={placeholder}
              {...props}
              sx={{
                position: "absolute",
                height: "auto",
                top: 0,
                right: 0,
                bottom: 0,
                left: 0,
                zIndex: 0,
                ...props.sx,
              }}
            />
          </Box>
          {/* <MenuButton
            as={Box}
            tabIndex={0}
            onKeyPress={(e) => {
              if (e.key === " ") {
                e.currentTarget.click();
              }
            }}
            onClick={(e) => console.log(e.target)}
            fontWeight="normal"
            size="sm"
            variant="outline"
            {...props}
            sx={{
              cursorEvents: "none",
              cursor: "pointer",
              border: "1px solid",
              borderColor: "gray.200",
              borderRadius: "md",
              padding: 2,
              "& span:first-child": {
                display: "flex",
                flexWrap: "wrap",
                gap: 2,
              },
              "&:active, &:hover": {
                bg: "none",
              },
              ...props.sx,
            }}
          >
            {selectedList.size > 0
              ? [...selectedList.keys()].map((key) => (
                  <Tag key={key} size="md">
                    <TagLabel>{key}</TagLabel>
                    <TagCloseButton onClick={(e) => console.log("click")} />
                  </Tag>
                ))
              : placeholder}
          </MenuButton> */}
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
  );
};
