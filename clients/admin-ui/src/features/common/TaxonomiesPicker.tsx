import {
  Badge,
  Box,
  CloseIcon,
  EditIcon,
  IconButton,
  SmallAddIcon,
  Wrap,
} from "fidesui";
import { useCallback, useState } from "react";
import TaxonomySelectDropdown from "~/features/common/dropdown/TaxonomySelectDropdown";
import { useOutsideClick } from "~/features/common/hooks";

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

  const handleClickOutside = useCallback(() => {
    setIsAdding(false);
  }, []);

  const { ref } = useOutsideClick(handleClickOutside);

  if (!selectedTaxonomies?.length) {
    return <Badge textTransform="none">None</Badge>;
  }

  return (
    <Wrap
      py={2}
      alignItems="center"
      position="relative"
      width="100%"
      gap={2}
      overflowX="auto"
      ref={ref}
    >
      {selectedTaxonomies.map((category) => (
        <Badge
          fontWeight="normal"
          textTransform="none"
          data-testid={`classification-${category}`}
          px={1.5}
          key={category}
        >
          {getDataCategoryDisplayName(category)}
          <IconButton
            onClick={() => onRemoveTaxonomy(category)}
            icon={<CloseIcon boxSize={2} />}
            size="2xs"
            mt={-0.5}
            ml={2}
            aria-label="Remove category"
          />
        </Badge>
      ))}
      <IconButton
        w="20px"
        h="20px"
        minW="20px"
        borderRadius="sm"
        icon={<SmallAddIcon />}
        onClick={() => setIsAdding(true)}
        data-testid="add-category-btn"
        aria-label="Add category"
      />

      {isAdding && (
        <Box
          className="select-wrapper"
          position="absolute"
          zIndex={10}
          top="0"
          left="0"
          width="100%"
          height="max"
          bgColor="#fff"
        >
          <TaxonomySelectDropdown
            onChange={(o) => {
              setIsAdding(false);
              onAddTaxonomy(o.value);
            }}
            menuIsOpen
          />
        </Box>
      )}
    </Wrap>
  );
};
export default TaxonomiesPicker;
