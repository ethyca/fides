import { Button, Divider, Flex, Icons, Popover, Typography } from "fidesui";
import { useMemo, useState } from "react";

import CheckboxTree from "~/features/common/CheckboxTree";
import { transformTaxonomyEntityToNodes } from "~/features/taxonomy/helpers";
import { DataCategory } from "~/types/api";

const { Text } = Typography;

interface Props {
  dataCategories: DataCategory[];
  checked: string[];
  onChecked: (newChecked: string[]) => void;
  buttonLabel?: string;
}

export const DataCategoryDropdown = ({
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
    <div className="max-h-[50vh] min-w-[300px] max-w-full overflow-y-auto">
      <div className="sticky top-0 z-10 pt-1">
        <Flex justify="space-between" className="mb-2 px-2">
          <Button
            size="small"
            className="mr-2 !w-auto"
            onClick={() => onChecked([])}
            data-testid="data-category-clear-btn"
          >
            Clear
          </Button>
          <Text className="mr-2">Data Categories</Text>
          <Button
            size="small"
            className="!w-auto"
            onClick={() => setOpen(false)}
            data-testid="data-category-done-btn"
          >
            Done
          </Button>
        </Flex>
        <Divider />
      </div>
      <div className="px-2" data-testid="data-category-checkbox-tree">
        <CheckboxTree
          nodes={dataCategoryNodes}
          selected={checked}
          onSelected={onChecked}
        />
      </div>
    </div>
  );

  return (
    <Popover
      content={content}
      trigger="click"
      open={open}
      onOpenChange={setOpen}
    >
      <Button
        icon={<Icons.ChevronDown />}
        className="!bg-transparent"
        block
        data-testid="data-category-dropdown"
      >
        {label}
      </Button>
    </Popover>
  );
};
