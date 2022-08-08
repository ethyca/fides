import {
  Box,
  Button,
  FormLabel,
  Grid,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  MenuOptionGroup,
  Stack,
  Text,
} from "@fidesui/react";
import { useMemo } from "react";

import { DataCategory } from "~/types/api";

import CheckboxTree from "../common/CheckboxTree";
import { ArrowDownLineIcon } from "../common/Icon";
import QuestionTooltip from "../common/QuestionTooltip";
import DataCategoryTag from "../taxonomy/DataCategoryTag";
import { transformTaxonomyEntityToNodes } from "../taxonomy/helpers";

interface Props {
  dataCategories: DataCategory[];
  checked: string[];
  onChecked: (newChecked: string[]) => void;
  tooltip?: string;
}

const DataCategoryDropdown = ({
  dataCategories,
  checked,
  onChecked,
}: Omit<Props, "tooltip">) => {
  const dataCategoryNodes = useMemo(
    () => transformTaxonomyEntityToNodes(dataCategories),
    [dataCategories]
  );

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
        data-testid="data-category-dropdown"
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
          <Box px={2}>
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

const DataCategoryInput = ({
  dataCategories,
  checked,
  onChecked,
  tooltip,
}: Props) => {
  const handleRemoveDataCategory = (dataCategoryName: string) => {
    onChecked(checked.filter((dc) => dc !== dataCategoryName));
  };

  const sortedCheckedDataCategories = checked
    .slice()
    .sort((a, b) => a.localeCompare(b));

  return (
    <Grid templateColumns="1fr 3fr">
      <FormLabel>Data Categories</FormLabel>
      <Stack>
        <Box display="flex" alignItems="center">
          <Box mr="2" width="100%">
            <DataCategoryDropdown
              dataCategories={dataCategories}
              checked={checked}
              onChecked={onChecked}
            />
          </Box>
          <QuestionTooltip label={tooltip} />
        </Box>
        <Stack data-testid="selected-categories">
          {sortedCheckedDataCategories.map((dc) => (
            <DataCategoryTag
              key={dc}
              name={dc}
              onClose={() => {
                handleRemoveDataCategory(dc);
              }}
            />
          ))}
        </Stack>
      </Stack>
    </Grid>
  );
};

export default DataCategoryInput;
