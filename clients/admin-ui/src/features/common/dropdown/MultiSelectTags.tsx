import {
  AntButton as Button,
  ArrowDownLineIcon,
  Box,
  Menu,
  MenuButton,
  MenuButtonProps,
  Tag,
  TagCloseButton,
  TagLabel,
} from "fidesui";
import { useMemo, useState } from "react";

import { createSelectedMap, getKeysFromMap } from "~/features/common/utils";

import MultiSelectDropdownList from "./MultiSelectDropdownList";

interface MultiSelectTagsProps<T>
  extends Omit<MenuButtonProps, "onChange" | "value"> {
  closeOnSelect?: boolean;
  options: Map<T, string>;
  value: T[] | undefined;
  placeholder?: string;
  onChange: (values: T[]) => void;
}

/**
 * Dropdown menu with a list of checkboxes for multiple selection that displays the selected values in a textbox as chips
 * @param closeOnSelect - Boolean to determine if the dropdown is to be immediately close on a user selection
 * @param options - Map of key/value pairs to be rendered as a checkbox list, where the value is the display text
 * @param onChange - Parent callback event handler invoked when list of selection values have changed
 * @param placeholder - Placeholder text to be displayed when no items are selected
 */
export const MultiSelectTags = <T extends string>({
  closeOnSelect = false,
  options,
  value,
  onChange,
  placeholder = "Select one or more items",
  ...props
}: MultiSelectTagsProps<T>) => {
  const [isOpen, setIsOpen] = useState(false);
  const list = useMemo(
    () => createSelectedMap<T>(options, value),
    [options, value],
  );
  const selectedList = useMemo(
    () => value?.map((selectedItem) => options.get(selectedItem)!),
    [options, value],
  );

  const handleClose = () => {
    setIsOpen(false);
  };
  const handleOpen = () => {
    setIsOpen(true);
  };

  const handleSelection = (items: Map<T, boolean>) => {
    const selectedLabels = getKeysFromMap(items, [true]);
    onChange(getKeysFromMap(options, selectedLabels));
    handleClose();
  };

  const handleRemoveItem = (item: T) => {
    onChange(value!.filter((selectedItem) => selectedItem !== item));
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
              zIndex: 0,
              ...props.sx,
            }}
          >
            {value?.length
              ? value.map((selectedItem) => (
                  <Tag key={selectedItem} size="md" zIndex={1}>
                    <TagLabel>{options.get(selectedItem)}</TagLabel>
                    <TagCloseButton
                      onClick={() => handleRemoveItem(selectedItem)}
                    />
                  </Tag>
                ))
              : placeholder}
            <MenuButton
              as={Button}
              icon={<ArrowDownLineIcon />}
              className="absolute right-0 top-0 border-none !bg-transparent"
            />
          </Box>
          {isOpen && (
            <MultiSelectDropdownList
              defaultValues={selectedList}
              items={list}
              onSelection={(items) => {
                handleSelection(items as Map<T, boolean>);
                onClose();
              }}
            />
          )}
        </>
      )}
    </Menu>
  );
};
