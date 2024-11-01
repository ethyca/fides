import { AntButton as Button, Box, CloseIcon } from "fidesui";
import { useCallback, useState } from "react";

import { TaxonomySelectOption } from "~/features/common/dropdown/DataCategorySelect";
import { useOutsideClick } from "~/features/common/hooks";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import TaxonomyBadge from "~/features/data-discovery-and-detection/ClassificationCategoryBadge";
import DataUseSelect from "~/features/data-discovery-and-detection/new-dataset-lifecycle/DataUseSelect";
import TaxonomyAddButton from "~/features/data-discovery-and-detection/tables/cells/TaxonomyAddButton";
import TaxonomyCellContainer from "~/features/data-discovery-and-detection/tables/cells/TaxonomyCellContainer";
import { useUpdateSystemMutation } from "~/features/system";
import { System } from "~/types/api";

interface EditDataUseCellProps {
  system: System;
}

const EditDataUseCell = ({ system }: EditDataUseCellProps) => {
  const [isAdding, setIsAdding] = useState(false);
  const { getDataUseDisplayName } = useTaxonomies();
  const [updateSystem] = useUpdateSystemMutation();

  const dataUses = system.privacy_declarations.map((pd) => pd.data_use);

  const handleClickOutside = useCallback(() => setIsAdding(false), []);

  const addDataUse = (use: TaxonomySelectOption) => {
    console.log("adding", use.value);
    setIsAdding(false);
  };
  const removeDataUse = (use: string) => console.log("removing", use);

  const { ref } = useOutsideClick(handleClickOutside);

  return (
    <TaxonomyCellContainer ref={ref}>
      {!isAdding && (
        <>
          {dataUses.map((d) => (
            <TaxonomyBadge key={d} data-testid={`data-use-${d}`}>
              {getDataUseDisplayName(d)}
              <Button
                onClick={() => removeDataUse(d)}
                icon={<CloseIcon boxSize={2} mt={-0.5} />}
                size="small"
                type="text"
                className="ml-1 max-h-4 max-w-4"
                aria-label="Remove data use"
              />
            </TaxonomyBadge>
          ))}
          <TaxonomyAddButton onClick={() => setIsAdding(true)} />
        </>
      )}
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
          <DataUseSelect onChange={addDataUse} menuIsOpen />
        </Box>
      )}
    </TaxonomyCellContainer>
  );
};

export default EditDataUseCell;
