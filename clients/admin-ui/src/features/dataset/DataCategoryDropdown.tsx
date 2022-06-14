import {
  Box,
  Button,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  MenuOptionGroup,
  Text,
} from "@fidesui/react";
import { useEffect, useMemo, useState } from "react";

import CheckboxTree from "../common/CheckboxTree";
import { ArrowDownLineIcon } from "../common/Icon";
import { transformDataCategoriesToNodes } from "../taxonomy/helpers";
import { DataCategory } from "../taxonomy/types";

interface Props {
  dataCategories: DataCategory[];
  checked: string[];
  onChecked: (newChecked: string[]) => void;
}

const DataCategoryDropdown = ({
  dataCategories,
  checked,
  onChecked,
}: Props) => {
  const dataCategoryNodes = useMemo(
    () => transformDataCategoriesToNodes(dataCategories),
    [dataCategories]
  );

  const [internalChecked, setInternalChecked] = useState(checked);

  useEffect(() => {
    // make sure this stays up to date with the parent `checked` since this is not the only
    // component that can control which items are checked
    setInternalChecked(checked);
  }, [checked]);

  const handleClear = () => {
    setInternalChecked([]);
  };

  return (
    <Menu closeOnSelect>
      <MenuButton
        as={Button}
        variant="outline"
        fontWeight="normal"
        size="sm"
        borderRadius="sm"
        textAlign="left"
        _hover={{ backgroundColor: "transparent" }}
        _active={{ backgroundColor: "transparent" }}
        rightIcon={<ArrowDownLineIcon />}
        width="100%"
      >
        Select data categories
      </MenuButton>
      <MenuList>
        <Box maxHeight="500px" minWidth="300px" overflowY="scroll">
          <Box
            position="sticky"
            top={0}
            zIndex={1}
            backgroundColor="white"
            pt={1}
          >
            <MenuOptionGroup>
              <Box display="flex" justifyContent="space-between" px={2} mb={2}>
                <MenuItem
                  as={Button}
                  variant="outline"
                  size="xs"
                  onClick={handleClear}
                  mr={2}
                  width="auto"
                  closeOnSelect={false}
                >
                  Clear
                </MenuItem>
                <Text mr={2}>Data Categories</Text>
                <MenuItem
                  as={Button}
                  size="xs"
                  colorScheme="primary"
                  color="white"
                  _hover={{ backgroundColor: "primary.600" }}
                  onClick={() => onChecked(internalChecked)}
                  width="auto"
                >
                  Done
                </MenuItem>
              </Box>
            </MenuOptionGroup>
            <MenuDivider />
          </Box>
          <Box px={2}>
            <CheckboxTree
              nodes={dataCategoryNodes}
              selected={internalChecked}
              onSelected={setInternalChecked}
            />
          </Box>
        </Box>
      </MenuList>
    </Menu>
  );
};

export default DataCategoryDropdown;
