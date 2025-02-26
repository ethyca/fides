import {
  AntSpace as Space,
  AntTag as Tag,
  Box,
  FormLabel,
  Grid,
} from "fidesui";

import { DataCategory } from "~/types/api";

import QuestionTooltip from "../common/QuestionTooltip";
import DataCategoryDropdown from "./DataCategoryDropdown";

export interface Props {
  dataCategories: DataCategory[];
  checked: string[];
  onChecked: (newChecked: string[]) => void;
  tooltip?: string;
}

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
      <Space direction="vertical" size="small">
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
        <Space direction="vertical" size={2} data-testid="selected-categories">
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
    </Grid>
  );
};

export default DataCategoryInput;
