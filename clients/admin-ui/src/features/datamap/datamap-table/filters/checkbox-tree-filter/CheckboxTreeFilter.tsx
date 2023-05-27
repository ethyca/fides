import { CheckboxTree } from "@fidesui/components";
import {
  Box,
  Button,
  FilterIcon,
  IconButton,
  Menu,
  MenuButton,
  MenuDivider,
  MenuList,
  Portal,
} from "@fidesui/react";
import { ColumnInstance } from "react-table";

import { DatamapRow } from "../../../datamap.slice";
import { useCheckboxTreeFilter } from "./helpers";

interface Props {
  column: ColumnInstance<DatamapRow>;
}

const CheckboxTreeFilter = ({ column }: Props) => {
  const { selected, nodes, onChangeSelected } = useCheckboxTreeFilter(column);

  return (
    <Menu isLazy closeOnSelect={false}>
      {({ onClose }) => (
        <>
          <MenuButton
            as={IconButton}
            icon={<FilterIcon width="16px" height="16px" />}
            size="sm"
            variant="ghost"
            aria-label="Column filters"
          />
          <Portal>
            <MenuList boxShadow="base">
              <Box display="flex" justifyContent="space-between" px={2}>
                <Button
                  variant="outline"
                  size="xs"
                  onClick={() => onChangeSelected([])}
                >
                  Clear
                </Button>
                <Button colorScheme="primary" size="xs" onClick={onClose}>
                  Done
                </Button>
              </Box>
              <MenuDivider />
              <CheckboxTree
                nodes={nodes}
                selected={selected}
                onSelected={onChangeSelected}
              />
            </MenuList>
          </Portal>
        </>
      )}
    </Menu>
  );
};

export default CheckboxTreeFilter;
