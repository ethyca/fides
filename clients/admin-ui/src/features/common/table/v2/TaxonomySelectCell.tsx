import { AntTag as Tag, Box } from "fidesui";
import { useState } from "react";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import TaxonomyCellContainer from "~/features/data-discovery-and-detection/tables/cells/TaxonomyCellContainer";

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
        <Tag
          key={category}
          data-testid={`classification-${category}`}
          color="white"
          closable
          onClose={() => onRemoveTaxonomy(category)}
          closeButtonLabel="Remove category"
        >
          {getDataCategoryDisplayName(category)}
        </Tag>
      ))}
      <Tag
        onClick={() => setIsAdding(true)}
        data-testid="add-category-btn"
        addable
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
