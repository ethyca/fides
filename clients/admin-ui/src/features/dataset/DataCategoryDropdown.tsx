import {
  Box,
  Button,
  Menu,
  MenuButton,
  MenuDivider,
  MenuList,
  Text,
} from "@fidesui/react";
import { useMemo, useState } from "react";

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

  const handleClear = () => {
    setInternalChecked([]);
  };

  return (
    <Menu>
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
      >
        Select data categories
      </MenuButton>
      <MenuList>
        <Box maxHeight="500px" minWidth="300px" overflowY="scroll">
          <Box position="sticky" top={0} zIndex={1} backgroundColor="white">
            <Box display="flex" justifyContent="space-between" px={2} mb={2}>
              <Button variant="outline" size="xs" onClick={handleClear} mr={2}>
                Clear
              </Button>
              <Text mr={2}>Data Categories</Text>
              <Button
                size="xs"
                colorScheme="primary"
                onClick={() => onChecked(internalChecked)}
              >
                Done
              </Button>
            </Box>
            <MenuDivider />
          </Box>
          <Box px={2}>
            <CheckboxTree
              nodes={dataCategoryNodes}
              checked={internalChecked}
              onChecked={setInternalChecked}
            />
          </Box>
        </Box>
      </MenuList>
    </Menu>
  );
};

export default DataCategoryDropdown;
