import { Flex } from "fidesui";
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
  const [isOpen, setIsOpen] = useState(false);
  const [currentDeclaration, setCurrentDeclaration] = useState<
    PrivacyDeclarationResponse | undefined
  >(undefined);
  const [isDirty, setIsDirty] = useState(false);

  const { createDataUse, updateDataUse, deleteDataUse } =
    useSystemDataUseCrud(system);

  const handleCloseForm = () => {
    setIsOpen(false);
    setCurrentDeclaration(undefined);
    setIsDirty(false);
  };

  const handleOpenNewForm = () => {
    setIsOpen(true);
    setCurrentDeclaration(undefined);
  };

  const handleOpenEditForm = (
    declarationToEdit: PrivacyDeclarationResponse,
  ) => {
    setIsOpen(true);
    setCurrentDeclaration(declarationToEdit);
  };

  const handleSubmit = async (values: PrivacyDeclarationResponse) => {
    handleCloseForm();
    if (currentDeclaration) {
      return updateDataUse(currentDeclaration, values);
    }
    return createDataUse(values);
  };

  // Reset modal state when the system changes (e.g. switching datamap nodes)
  useEffect(() => {
    setIsOpen(false);
    setCurrentDeclaration(undefined);
    setIsDirty(false);
  }, [system.fides_key]);

  return (
    <Flex vertical gap="large" data-testid="data-use-tab">
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
        getIsDirty={() => isDirty}
      >
        <PrivacyDeclarationForm
          initialValues={currentDeclaration}
          onSubmit={handleSubmit}
          onCancel={handleCloseForm}
          onDirtyChange={setIsDirty}
          includeCustomFields={includeCustomFields}
          {...dataProps}
        />
      </PrivacyDeclarationFormModal>
    </Flex>
  );
};

export default PrivacyDeclarationFormTab;
