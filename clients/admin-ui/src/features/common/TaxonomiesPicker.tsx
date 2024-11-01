import {
  AntButton as Button,
  Badge,
  Box,
  CloseIcon,
  SmallAddIcon,
  Wrap,
} from "fidesui";
import { useCallback, useState } from "react";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
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
