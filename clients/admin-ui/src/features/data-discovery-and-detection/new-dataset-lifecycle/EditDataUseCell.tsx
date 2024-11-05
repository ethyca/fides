import { AntButton as Button, Box, CloseIcon, EditIcon } from "fidesui";
import { useCallback, useState } from "react";

import { TaxonomySelectOption } from "~/features/common/dropdown/TaxonomyDropdownOption";
import { useOutsideClick } from "~/features/common/hooks";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import TaxonomyBadge from "~/features/data-discovery-and-detection/ClassificationCategoryBadge";
import DataUseSelect from "~/features/data-discovery-and-detection/new-dataset-lifecycle/DataUseSelect";
import TaxonomyAddButton from "~/features/data-discovery-and-detection/tables/cells/TaxonomyAddButton";
import TaxonomyCellContainer from "~/features/data-discovery-and-detection/tables/cells/TaxonomyCellContainer";
import useSystemDataUseCrud from "~/features/data-use/useSystemDataUseCrud";
import { SystemResponse } from "~/types/api";
import { PrivacyDeclaration } from "~/types/dictionary-api";

interface EditDataUseCellProps {
  system: SystemResponse;
}

const createMinimalDataUse = (use: string): PrivacyDeclaration => ({
  data_use: use,
  data_categories: ["system"],
});

const EditDataUseCell = ({ system }: EditDataUseCellProps) => {
  console.log(system.privacy_declarations);
  const [isAdding, setIsAdding] = useState(false);
  const { getDataUseDisplayName } = useTaxonomies();

  const { createDataUse, deleteDeclarationByDataUse, updateDataUse } =
    useSystemDataUseCrud(system);

  const dataUses = system.privacy_declarations.map((pd) => pd.data_use);

  const handleClickOutside = useCallback(() => setIsAdding(false), []);

  const addDataUse = (use: TaxonomySelectOption) => {
    const declaration = createMinimalDataUse(use.value);
    createDataUse(declaration);
    setIsAdding(false);
  };

  const { ref } = useOutsideClick(handleClickOutside);

  return (
    <TaxonomyCellContainer ref={ref}>
      {!isAdding && (
        <>
          {dataUses.map((d) => (
            <TaxonomyBadge
              key={d}
              data-testid={`data-use-${d}`}
              onClick={() => console.log(`editing ${d}...`)}
            >
              <EditIcon />
              {getDataUseDisplayName(d)}
              <Button
                onClick={() => deleteDeclarationByDataUse(d)}
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
