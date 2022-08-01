import {
  Box,
  Button,
  Flex,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
  Tooltip,
} from "@fidesui/react";
import { useState } from "react";

import { ArrowDownLineIcon } from "../Icon";
import { ItemOption } from "./types";

type SelectDropdownProps = {
  /**
   * List of key/value pair items
   */
  list: Map<string, ItemOption>;
  /**
   * Parent callback event handler invoked when selected value has changed
   */
  onChange: (value: string | undefined) => void;
  /**
   * Placeholder
   */
  label: string;
  /**
   * Display the Clear button. Default value is true.
   */
  hasClear?: boolean;
  /**
   * Default value marked for selection
   */
  selectedValue?: string;
  /**
   * Width of an element
   */
  width?: string;
};

const SelectDropdown: React.FC<SelectDropdownProps> = ({
  hasClear = true,
  label,
  list,
  onChange,
  selectedValue,
  width,
}) => {
  // Hooks
  const [isOpen, setIsOpen] = useState(false);

  // Listeners
  const handleClose = () => {
    setIsOpen(false);
  };
  const handleClear = () => {
    onChange(undefined);
    handleClose();
  };
  const handleOpen = () => {
    setIsOpen(true);
  };

  const selectedText = [...list].find(
    ([, option]) => option.value === selectedValue
  )?.[0];

  return (
    <Box>
      <Menu isLazy onClose={handleClose} onOpen={handleOpen}>
        <MenuButton
          aria-label={selectedText ?? label}
          as={Button}
          color={selectedText ? "complimentary.500" : undefined}
          fontWeight="normal"
          rightIcon={<ArrowDownLineIcon />}
          size="sm"
          variant="outline"
          width={width}
          _active={{
            bg: "none",
          }}
          _hover={{
            bg: "none",
          }}
        >
          <Text isTruncated>{selectedText ?? label}</Text>
        </MenuButton>
        {isOpen ? (
          <MenuList lineHeight="1rem" p="0">
            {hasClear && (
              <Flex
                borderBottom="1px"
                borderColor="gray.200"
                cursor="auto"
                p="8px"
              >
                <Button onClick={handleClear} size="xs" variant="outline">
                  Clear
                </Button>
              </Flex>
            )}
            {/* MenuItems are not rendered unless Menu is open */}
            {[...list].sort().map(([key, option]) => (
              <Tooltip
                aria-label={option.toolTip}
                hasArrow
                label={option.toolTip}
                key={key}
                placement="auto-start"
                openDelay={500}
                shouldWrapChildren
              >
                <MenuItem
                  color={
                    selectedValue === option.value
                      ? "complimentary.500"
                      : undefined
                  }
                  isDisabled={option.isDisabled}
                  onClick={() => onChange(option.value)}
                  paddingTop="10px"
                  paddingRight="8.5px"
                  paddingBottom="10px"
                  paddingLeft="8.5px"
                  _focus={{
                    bg: "gray.100",
                  }}
                >
                  <Text fontSize="0.75rem">{key}</Text>
                </MenuItem>
              </Tooltip>
            ))}
          </MenuList>
        ) : null}
      </Menu>
    </Box>
  );
};

export default SelectDropdown;
