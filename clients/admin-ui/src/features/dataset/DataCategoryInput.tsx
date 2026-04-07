import { Col, Flex, Row, Space, Tag } from "fidesui";

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
    <Row>
      <Col span={6}>
        <span>Data Categories</span>
      </Col>
      <Col span={18}>
        <Space direction="vertical" size="small" className="w-full">
          <Flex align="center">
            <div className="mr-2 w-full">
              <DataCategoryDropdown
                dataCategories={dataCategories}
                checked={checked}
                onChecked={onChecked}
              />
            </div>
            <InfoTooltip label={tooltip} />
          </Flex>
          <Space
            direction="vertical"
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
      </Col>
    </Row>
  );
};
