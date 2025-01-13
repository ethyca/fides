import {
  AntButton as Button,
  Badge,
  Box,
  CloseIcon,
  SmallAddIcon,
  Wrap,
} from "fidesui";
import { useState } from "react";

import { TaxonomySelect } from "~/features/common/dropdown/TaxonomySelect";

import useTaxonomies from "./hooks/useTaxonomies";

interface TaxonomiesPickerProps {
  selectedTaxonomies: string[];
  onAddTaxonomy: (taxonomy: string) => void;
  onRemoveTaxonomy: (taxonomy: string) => void;
}

const TaxonomiesPicker = ({
  selectedTaxonomies,
  onAddTaxonomy,
  onRemoveTaxonomy,
}: TaxonomiesPickerProps) => {
  const [isAdding, setIsAdding] = useState(false);
  const { getDataCategoryDisplayName } = useTaxonomies();

  return (
    <Wrap
      py={2}
      alignItems="center"
      position="relative"
      width="100%"
      gap={2}
      overflowX="auto"
    >
      {selectedTaxonomies.map((category) => (
        <Badge
          fontWeight="normal"
          textTransform="none"
          data-testid={`classification-${category}`}
          px={1.5}
          key={category}
          variant="taxonomy"
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
        icon={<SmallAddIcon mb="1px" />}
        onClick={() => setIsAdding(true)}
        className="max-h-[22px] max-w-[22px]"
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
          <TaxonomySelect
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
    </Wrap>
  );
};
export default TaxonomiesPicker;
