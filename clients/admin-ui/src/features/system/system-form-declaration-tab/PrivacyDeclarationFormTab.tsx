import { Box, ButtonProps, Divider, Stack, Text, useDisclosure } from "fidesui";
import { Fragment, useEffect, useState } from "react";

import useSystemDataUseCrud from "~/features/data-use/useSystemDataUseCrud";
import EmptyTableState from "~/features/system/dictionary-data-uses/EmptyTableState";
import { transformDictDataUseToDeclaration } from "~/features/system/dictionary-form/helpers";
import {
  PrivacyDeclarationDisplayGroup,
  PrivacyDeclarationTabTable,
} from "~/features/system/system-form-declaration-tab/PrivacyDeclarationDisplayGroup";
import {
  DataProps,
  PrivacyDeclarationForm,
} from "~/features/system/system-form-declaration-tab/PrivacyDeclarationForm";
import { PrivacyDeclarationFormModal } from "~/features/system/system-form-declaration-tab/PrivacyDeclarationFormModal";
import { PrivacyDeclarationResponse, SystemResponse } from "~/types/api";
import { DataUseDeclaration } from "~/types/dictionary-api";

import PrivacyDeclarationDictModalComponents from "../dictionary-data-uses/PrivacyDeclarationDictModalComponents";

interface Props {
  system: SystemResponse;
  addButtonProps?: ButtonProps;
  includeCustomFields?: boolean;
  includeCookies?: boolean;
}

const PrivacyDeclarationFormTab = ({
  system,
  addButtonProps,
  includeCustomFields,
  includeCookies,
  ...dataProps
}: Props & DataProps) => {
  const [showForm, setShowForm] = useState(false);
  const [currentDeclaration, setCurrentDeclaration] = useState<
    PrivacyDeclarationResponse | undefined
  >(undefined);

  const { isOpen: showDictionaryModal, onClose: handleCloseDictModal } =
    useDisclosure();

  const { patchDataUses, createDataUse, updateDataUse, deleteDataUse } =
    useSystemDataUseCrud(system);

  const assignedCookies = [
    ...system.privacy_declarations
      .filter((d) => d.cookies !== undefined)
      .flatMap((d) => d.cookies),
  ];

  const unassignedCookies = system.cookies
    ? system.cookies.filter(
        (c) =>
          assignedCookies.filter(
            (assigned) => assigned && assigned.name === c.name,
          ).length === 0,
      )
    : undefined;

  const handleCloseForm = () => {
    setShowForm(false);
    setCurrentDeclaration(undefined);
  };

  const handleOpenNewForm = () => {
    setShowForm(true);
    setCurrentDeclaration(undefined);
  };

  const handleOpenEditForm = (
    declarationToEdit: PrivacyDeclarationResponse,
  ) => {
    setShowForm(true);
    setCurrentDeclaration(declarationToEdit);
  };

  const handleAcceptDictSuggestions = (suggestions: DataUseDeclaration[]) => {
    const newDeclarations = suggestions.map((du) =>
      transformDictDataUseToDeclaration(du),
    );

    patchDataUses(newDeclarations);
    handleCloseDictModal();
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
    setShowForm(false);
  }, [system.fides_key]);

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
      {unassignedCookies && unassignedCookies.length > 0 ? (
        <PrivacyDeclarationTabTable heading="Unassigned cookies">
          {unassignedCookies.map((cookie) => (
            <Fragment key={cookie.name}>
              <Box px={6} py={4}>
                <Text>{cookie.name}</Text>
              </Box>
              <Divider />
            </Fragment>
          ))}
        </PrivacyDeclarationTabTable>
      ) : null}
      <PrivacyDeclarationFormModal
        isOpen={showForm}
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
      {system.vendor_id ? (
        <PrivacyDeclarationFormModal
          isOpen={showDictionaryModal}
          onClose={handleCloseDictModal}
          isCentered
          heading="Compass suggestions"
        >
          <PrivacyDeclarationDictModalComponents
            alreadyHasDataUses={system.privacy_declarations.length > 0}
            allDataUses={dataProps.allDataUses}
            onCancel={handleCloseDictModal}
            onAccept={handleAcceptDictSuggestions}
            vendorId={system.vendor_id}
          />
        </PrivacyDeclarationFormModal>
      ) : null}
    </Stack>
  );
};

export default PrivacyDeclarationFormTab;
