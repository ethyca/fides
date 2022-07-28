import {
  Box,
  Button,
  Flex,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
} from "@fidesui/react";
import { useState } from "react";

import { ArrowDownLineIcon } from "../Icon";

type SelectDropdownProps = {
  /**
   * List of key/value pair items
   */
  list: Map<string, string>;
  /**
   * Parent callback event handler invoked when selected value has changed
   */
  onChange: (value: string | undefined) => void;
  /**
   * Placeholder
   */
  label: string;
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

  const selectedText = [...list].find(([, v]) => v === selectedValue)?.[0];

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
          _focus={{
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
            </Flex>
            {/* MenuItems are not rendered unless Menu is open */}
            {[...list].sort().map(([key, value]) => (
              <MenuItem
                color={
                  selectedValue === value ? "complimentary.500" : undefined
                }
                key={key}
                onClick={() => onChange(value)}
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
            ))}
          </MenuList>
        ) : null}
      </Menu>
    </Box>
  );
};

export default SelectDropdown;
