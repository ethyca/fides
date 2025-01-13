import {
  AntButton as Button,
  Badge,
  Box,
  CloseIcon,
  SmallAddIcon,
} from "fidesui";
import { useState } from "react";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import TaxonomyCellContainer from "~/features/data-discovery-and-detection/tables/cells/TaxonomyCellContainer";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";

interface TaxonomyCellProps {
  selectedTaxonomies: string[];
  onAddTaxonomy: (taxonomy: string) => void;
  onRemoveTaxonomy: (taxonomy: string) => void;
}

const TaxonomySelectCell = ({
  selectedTaxonomies,
  onAddTaxonomy,
  onRemoveTaxonomy,
}: TaxonomyCellProps) => {
  const [isAdding, setIsAdding] = useState(false);
  const { getDataCategoryDisplayName } = useTaxonomies();

  return (
    <TaxonomyCellContainer>
      {selectedTaxonomies.map((category) => (
        <Badge
          fontWeight="normal"
          textTransform="none"
          data-testid={`classification-${category}`}
          px={1.5}
          key={category}
        >
          {getDataCategoryDisplayName(category)}
          <Button
            onClick={() => onRemoveTaxonomy(category)}
            icon={<CloseIcon boxSize={2} />}
            size="small"
            type="text"
            className="ml-1 max-h-4 max-w-4"
            aria-label="Remove category"
          />
        </Badge>
      ))}
      <Button
        size="small"
        type="text"
        icon={<SmallAddIcon mb="1px" />}
        onClick={() => setIsAdding(true)}
        className=" max-h-[20px] max-w-[20px] rounded-sm border-none bg-gray-100 hover:!bg-gray-200"
        data-testid="add-category-btn"
        aria-label="Add category"
      />

      {isAdding && (
        <Box
          // eslint-disable-next-line tailwindcss/no-custom-classname
          className="select-wrapper"
          position="absolute"
          zIndex={10}
          top="0"
          left="0"
          width="100%"
          height="max"
          bgColor="#fff"
        >
          <DataCategorySelect
            selectedTaxonomies={selectedTaxonomies}
            onChange={(o) => {
              setIsAdding(false);
              onAddTaxonomy(o);
            }}
            onBlur={() => setIsAdding(false)}
            open={isAdding}
          />
        </Box>
      )}
    </TaxonomyCellContainer>
  );
};
export default TaxonomySelectCell;
