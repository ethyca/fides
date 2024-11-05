import {
  Box,
  ClassifiedDataCategoryDropdown,
  FormLabel,
  Grid,
  Stack,
} from "fidesui";

import { DataCategory } from "~/types/api";

import QuestionTooltip from "../common/QuestionTooltip";
import TaxonomyEntityTag from "../taxonomy/TaxonomyEntityTag";
import DataCategoryDropdown from "./DataCategoryDropdown";

export interface Props {
  dataCategories: DataCategory[];
  mostLikelyCategories?: DataCategory[];
  checked: string[];
  onChecked: (newChecked: string[]) => void;
  tooltip?: string;
}

const DataCategoryInput = ({
  dataCategories,
  mostLikelyCategories,
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
      {mostLikelyCategories ? (
        <Box display="flex" alignItems="center">
          <Box mr="2" width="100%">
            <ClassifiedDataCategoryDropdown
              dataCategories={dataCategories}
              mostLikelyCategories={mostLikelyCategories}
              checked={checked}
              onChecked={onChecked}
            />
          </Box>
          <QuestionTooltip label={tooltip} />
        </Box>
      ) : (
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
              <TaxonomyEntityTag
                key={dc}
                name={dc}
                onClose={() => {
                  handleRemoveDataCategory(dc);
                }}
              />
            ))}
          </Stack>
        </Stack>
      )}
    </Grid>
  );
};

export default DataCategoryInput;
