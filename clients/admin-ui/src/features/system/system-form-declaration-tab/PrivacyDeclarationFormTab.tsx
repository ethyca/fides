import { Stack, useDisclosure } from "fidesui";
import { useEffect, useState } from "react";

import useSystemDataUseCrud from "~/features/data-use/useSystemDataUseCrud";
import EmptyTableState from "~/features/system/system-form-declaration-tab/EmptyTableState";
import { PrivacyDeclarationDisplayGroup } from "~/features/system/system-form-declaration-tab/PrivacyDeclarationDisplayGroup";
import {
  DataProps,
  PrivacyDeclarationForm,
} from "~/features/system/system-form-declaration-tab/PrivacyDeclarationForm";
import { PrivacyDeclarationFormModal } from "~/features/system/system-form-declaration-tab/PrivacyDeclarationFormModal";
import { PrivacyDeclarationResponse, SystemResponse } from "~/types/api";

interface Props {
  system: SystemResponse;
  includeCustomFields?: boolean;
}

const PrivacyDeclarationFormTab = ({
  system,
  includeCustomFields,
  ...dataProps
}: Props & DataProps) => {
  const { isOpen, onClose, onOpen } = useDisclosure();
  const [currentDeclaration, setCurrentDeclaration] = useState<
    PrivacyDeclarationResponse | undefined
  >(undefined);

  const { createDataUse, updateDataUse, deleteDataUse } =
    useSystemDataUseCrud(system);

  const handleCloseForm = () => {
    onClose();
    setCurrentDeclaration(undefined);
  };

  const handleOpenNewForm = () => {
    onOpen();
    setCurrentDeclaration(undefined);
  };

  const handleOpenEditForm = (
    declarationToEdit: PrivacyDeclarationResponse,
  ) => {
    onOpen();
    setCurrentDeclaration(declarationToEdit);
  };

  const handleSubmit = async (values: PrivacyDeclarationResponse) => {
    handleCloseForm();
    if (currentDeclaration) {
      return updateDataUse(currentDeclaration, values);
    }
    return createDataUse(values);
  };

  // Reset the new form when the system changes (i.e. when clicking on a new datamap node)
  useEffect(() => {
    onClose();
  }, [onClose, system.fides_key]);

  return (
    <Stack spacing={6} data-testid="data-use-tab">
      {system.privacy_declarations.length === 0 ? (
        <EmptyTableState
          title="You don't have a data use set up for this system yet."
          description='A Data Use is the purpose for which data is used in a system. In Fides, a system may have more than one Data Use. For example, a CRM system may be used both for "Customer Support" and also for "Email Marketing", each of these is a Data Use.'
          handleAdd={handleOpenNewForm}
        />
      ) : (
        <PrivacyDeclarationDisplayGroup
          heading="Data use"
          declarations={system.privacy_declarations}
          handleAdd={handleOpenNewForm}
          handleEdit={handleOpenEditForm}
          handleDelete={deleteDataUse}
          allDataUses={dataProps.allDataUses}
        />
      )}
      <PrivacyDeclarationFormModal
        isOpen={isOpen}
        onClose={handleCloseForm}
        heading="Configure data use"
      >
        <PrivacyDeclarationForm
          initialValues={currentDeclaration}
          onSubmit={handleSubmit}
          onCancel={handleCloseForm}
          includeCustomFields={includeCustomFields}
          {...dataProps}
        />
      </PrivacyDeclarationFormModal>
    </Stack>
  );
};

export default PrivacyDeclarationFormTab;
