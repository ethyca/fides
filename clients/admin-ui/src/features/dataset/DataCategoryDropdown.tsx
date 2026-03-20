import {
  ArrowDownLineIcon,
  Button,
  ChakraBox as Box,
  ChakraText as Text,
  Divider,
  Popover,
} from "fidesui";
import { useMemo, useState } from "react";

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
  const [open, setOpen] = useState(false);

  const dataCategoryNodes = useMemo(
    () => transformTaxonomyEntityToNodes(dataCategories),
    [dataCategories],
  );

  const label = buttonLabel ?? "Select data categories";

  const content = (
    <Box maxHeight="50vh" minWidth="300px" maxW="full" overflowY="scroll">
      <Box position="sticky" top={0} zIndex={1} backgroundColor="white" pt={1}>
        <Box display="flex" justifyContent="space-between" px={2} mb={2}>
          <Button
            size="small"
            className="mr-2 !w-auto"
            onClick={() => onChecked([])}
            data-testid="data-category-clear-btn"
          >
            Clear
          </Button>
          <Text mr={2}>Data Categories</Text>
          <Button
            size="small"
            className="!w-auto"
            onClick={() => setOpen(false)}
            data-testid="data-category-done-btn"
          >
            Done
          </Button>
        </Box>
        <Divider />
      </Box>
      <Box px={2} data-testid="data-category-checkbox-tree">
        <CheckboxTree
          nodes={dataCategoryNodes}
          selected={checked}
          onSelected={onChecked}
        />
      </Box>
    </Box>
  );

  return (
    <Popover
      content={content}
      trigger="click"
      open={open}
      onOpenChange={setOpen}
      styles={{ content: { padding: 0 } }}
    >
      <Button
        icon={<ArrowDownLineIcon />}
        className="!bg-transparent"
        block
        data-testid="data-category-dropdown"
      >
        {label}
      </Button>
    </Popover>
  );
};

export default DataCategoryDropdown;
