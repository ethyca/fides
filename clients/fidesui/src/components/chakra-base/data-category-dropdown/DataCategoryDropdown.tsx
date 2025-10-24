import {
  ArrowDownLineIcon,
  Box,
  Button,
  ButtonProps,
  Menu,
  MenuButton,
  MenuButtonProps,
  MenuDivider,
  MenuItem,
  MenuList,
  MenuOptionGroup,
  Text,
} from "fidesui";
import React, { useMemo } from "react";

import { CheckboxTree } from "../checkbox-tree";
import { DataCategory } from "../types/api";
import { transformTaxonomyEntityToNodes } from "./helpers";

interface Props {
  dataCategories: DataCategory[];
  checked: string[];
  onChecked: (newChecked: string[]) => void;
  buttonProps?: ButtonProps;
  buttonLabel?: string;
}

export const DataCategoryDropdown = ({
  dataCategories,
  checked,
  onChecked,
  buttonProps,
  buttonLabel,
}: Props) => {
  const dataCategoryNodes = useMemo(
    () => transformTaxonomyEntityToNodes(dataCategories),
    [dataCategories],
  );

  const defaultButtonProps: ButtonProps = {
    variant: "outline",
    fontWeight: "normal",
    size: "sm",
    borderRadius: "sm",
    textAlign: "left",
    _hover: { backgroundColor: "transparent" },
    _active: { backgroundColor: "transparent" },
    rightIcon: <ArrowDownLineIcon />,
    width: "100%",
  };
  const menuButtonProps = buttonProps ?? defaultButtonProps;
  const label = buttonLabel ?? "Select data categories";

  return (
    <Menu closeOnSelect>
      <MenuButton
        as={Button}
        {...(menuButtonProps as MenuButtonProps)}
        data-testid="data-category-dropdown"
      >
        {label}
      </MenuButton>
      <MenuList>
        <Box maxHeight="50vh" minWidth="300px" overflowY="scroll">
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
                  onClick={() => onChecked([])}
                  mr={2}
                  width="auto"
                  closeOnSelect={false}
                  data-testid="data-category-clear-btn"
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
                  width="auto"
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
