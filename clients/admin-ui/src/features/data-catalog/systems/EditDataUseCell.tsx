import {
  AntButton as Button,
  Box,
  CloseIcon,
  EditIcon,
  useDisclosure,
} from "fidesui";
import { useState } from "react";

import DataUseSelect from "~/features/common/dropdown/DataUseSelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import EditMinimalDataUseModal from "~/features/data-catalog/systems/EditMinimalDataUseModal";
import TaxonomyAddButton from "~/features/data-discovery-and-detection/tables/cells/TaxonomyAddButton";
import TaxonomyCellContainer from "~/features/data-discovery-and-detection/tables/cells/TaxonomyCellContainer";
import TaxonomyBadge from "~/features/data-discovery-and-detection/TaxonomyBadge";
import useSystemDataUseCrud from "~/features/data-use/useSystemDataUseCrud";
import {
  PrivacyDeclaration,
  PrivacyDeclarationResponse,
  SystemResponse,
} from "~/types/api";

interface EditDataUseCellProps {
  system: SystemResponse;
}

const DeleteDataUseButton = ({ onClick }: { onClick: () => void }) => (
  <Button
    onClick={onClick}
    icon={<CloseIcon boxSize={2} />}
    size="small"
    type="text"
    className="max-h-4 max-w-4"
    aria-label="Remove data use"
  />
);

const createMinimalDataUse = (use: string): PrivacyDeclaration => ({
  data_use: use,
  data_categories: ["system"],
});

const EditDataUseCell = ({ system }: EditDataUseCellProps) => {
  const [isAdding, setIsAdding] = useState(false);
  const [declarationToEdit, setDeclarationToEdit] = useState<
    PrivacyDeclarationResponse | undefined
  >(undefined);

  const { getDataUseDisplayName } = useTaxonomies();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const handleOpenEditForm = (declaration: PrivacyDeclarationResponse) => {
    setDeclarationToEdit(declaration);
    onOpen();
  };

  const { createDataUse, deleteDeclarationByDataUse, updateDataUse } =
    useSystemDataUseCrud(system);

  const dataUses = system.privacy_declarations?.map((pd) => pd.data_use) ?? [];

  const addDataUse = (use: string) => {
    const declaration = createMinimalDataUse(use);
    createDataUse(declaration);
    setIsAdding(false);
  };

  return (
    <TaxonomyCellContainer>
      {!isAdding && (
        <>
          {dataUses.map((d, idx) => (
            <TaxonomyBadge
              key={d}
              data-testid={`data-use-${d}`}
              onClick={() =>
                handleOpenEditForm(system.privacy_declarations[idx])
              }
              closeButton={
                <DeleteDataUseButton
                  onClick={() => deleteDeclarationByDataUse(d)}
                />
              }
            >
              <EditIcon />
              {getDataUseDisplayName(d)}
            </TaxonomyBadge>
          ))}
          <TaxonomyAddButton
            onClick={() => setIsAdding(true)}
            aria-label="Add data use"
          />
          <EditMinimalDataUseModal
            isOpen={isOpen}
            onClose={onClose}
            onSave={(values) => updateDataUse(declarationToEdit!, values)}
            declaration={declarationToEdit!}
          />
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
          <DataUseSelect
            onChange={addDataUse}
            selectedTaxonomies={dataUses}
            onBlur={() => setIsAdding(false)}
            open
          />
        </Box>
      )}
    </TaxonomyCellContainer>
  );
};

export default EditDataUseCell;
