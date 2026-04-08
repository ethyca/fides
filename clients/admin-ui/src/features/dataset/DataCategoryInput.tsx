import { Flex, Form, Space, Tag } from "fidesui";

import { DataCategory } from "~/types/api";

import { InfoTooltip } from "../common/InfoTooltip";
import { DataCategoryDropdown } from "./DataCategoryDropdown";

export interface Props {
  dataCategories: DataCategory[];
  checked: string[];
  onChecked: (newChecked: string[]) => void;
  tooltip?: string;
}

export const DataCategoryInput = ({
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
    <Form.Item
      label={
        <Flex align="center" gap="small">
          Data Categories
          <InfoTooltip label={tooltip} />
        </Flex>
      }
    >
      <Space orientation="vertical" size="small" className="w-full">
        <DataCategoryDropdown
          dataCategories={dataCategories}
          checked={checked}
          onChecked={onChecked}
        />
        <Space
          orientation="vertical"
          size={2}
          data-testid="selected-categories"
        >
          {sortedCheckedDataCategories.map((dc) => (
            <Tag
              closable
              onClose={() => {
                handleRemoveDataCategory(dc);
              }}
              key={dc}
            >
              {dc}
            </Tag>
          ))}
        </Space>
      </Space>
    </Form.Item>
  );
};
