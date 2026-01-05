import {
  ArrowDownLineIcon,
  Button,
  ChakraBox as Box,
  ChakraMenu as Menu,
  ChakraMenuButton as MenuButton,
  ChakraMenuDivider as MenuDivider,
  ChakraMenuItem as MenuItem,
  ChakraMenuList as MenuList,
  ChakraMenuOptionGroup as MenuOptionGroup,
  ChakraText as Text,
} from "fidesui";
import { useMemo } from "react";

import CheckboxTree from "~/features/common/CheckboxTree";
import { transformTaxonomyEntityToNodes } from "~/features/taxonomy/helpers";
import { DataCategory } from "~/types/api";

interface Props {
  dataCategories: DataCategory[];
  checked: string[];
  onChecked: (newChecked: string[]) => void;
  buttonLabel?: string;
}

const DataCategoryDropdown = ({
  dataCategories,
  checked,
  onChecked,
  buttonLabel,
}: Props) => {
  const dataCategoryNodes = useMemo(
    () => transformTaxonomyEntityToNodes(dataCategories),
    [dataCategories],
  );

  const label = buttonLabel ?? "Select data categories";

  return (
    <Menu closeOnSelect>
      <MenuButton
        as={Button}
        icon={<ArrowDownLineIcon />}
        className="!bg-transparent"
        block
        data-testid="data-category-dropdown"
      >
        {label}
      </MenuButton>
      <MenuList>
        <Box maxHeight="50vh" minWidth="300px" maxW="full" overflowY="scroll">
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
                  size="small"
                  className="mr-2 !w-auto"
                  onClick={() => onChecked([])}
                  closeOnSelect={false}
                  data-testid="data-category-clear-btn"
                >
                  Clear
                </MenuItem>
                <Text mr={2}>Data Categories</Text>
                <MenuItem
                  as={Button}
                  size="small"
                  className="!w-auto"
                  data-testid="data-category-done-btn"
                >
                  Done
                </MenuItem>
              </Box>
            </MenuOptionGroup>
            <MenuDivider />
          </Box>
          <Box px={2} data-testid="data-category-checkbox-tree">
            <CheckboxTree
              nodes={dataCategoryNodes}
              selected={checked}
              onSelected={onChecked}
            />
          </Box>
        </Box>
      </MenuList>
    </Menu>
  );
};

export default DataCategoryDropdown;
