import { Box, Button, Stack, Tooltip, useToast } from "@fidesui/react";
import { useMemo, useState } from "react";

import { PrivacyDeclaration, System } from "~/types/api";

import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";
import { DataProps, PrivacyDeclarationForm } from "./PrivacyDeclarationForm";

type FormValues = PrivacyDeclaration;

const transformFormValuesToDeclaration = (
  formValues: FormValues
): PrivacyDeclaration => ({
  ...formValues,
  // Fill in an empty string for name because of https://github.com/ethyca/fideslang/issues/98
  name: formValues.name ?? "",
});

interface Props {
  system: System;
  onCollision: () => void;
  onSave: (
    privacyDeclarations: PrivacyDeclaration[],
    isDelete?: boolean
  ) => Promise<boolean>;
}

const PrivacyDeclarationManager = ({
  system,
  onCollision,
  onSave,
  ...dataProps
}: Props & DataProps) => {
  const toast = useToast();

  const [showNewForm, setShowNewForm] = useState(false);
  const [newDeclaration, setNewDeclaration] = useState<
    PrivacyDeclaration | undefined
  >(undefined);

  const accordionDeclarations = useMemo(() => {
    if (!newDeclaration) {
      return system.privacy_declarations;
    }
    return system.privacy_declarations.filter(
      (pd) =>
        pd.name !== newDeclaration.name ||
        pd.data_use !== newDeclaration.data_use
    );
  }, [newDeclaration, system]);

  const checkAlreadyExists = (values: PrivacyDeclaration) => {
    if (
      accordionDeclarations.filter((d) =>
        values.name
          ? d.name === values.name && d.data_use === values.data_use
          : d.data_use === values.data_use && d.name === ""
      ).length > 0
    ) {
      onCollision();
      return true;
    }
    return false;
  };

  const handleSave = async (
    updatedDeclarations: PrivacyDeclaration[],
    isDelete?: boolean
  ) => {
    const transformedDeclarations = updatedDeclarations.map((d) =>
      transformFormValuesToDeclaration(d)
    );
    const success = await onSave(transformedDeclarations, isDelete);
    return success;
  };

  const handleEditDeclaration = async (
    oldDeclaration: PrivacyDeclaration,
    updatedDeclaration: PrivacyDeclaration
  ) => {
    // Do not allow editing a privacy declaration to have the same data use as one that already exists
    if (
      updatedDeclaration.data_use !== oldDeclaration.data_use &&
      checkAlreadyExists(updatedDeclaration)
    ) {
      return false;
    }
    // Because the data use can change, we also need a reference to the old declaration in order to
    // make sure we are replacing the proper one
    const updatedDeclarations = accordionDeclarations.map((dec) =>
      dec.name === oldDeclaration.name &&
      dec.data_use === oldDeclaration.data_use
        ? updatedDeclaration
        : dec
    );
    return handleSave(updatedDeclarations);
  };

  const saveNewDeclaration = async (values: PrivacyDeclaration) => {
    if (checkAlreadyExists(values)) {
      return false;
    }

    toast.closeAll();
    setNewDeclaration(values);
    const updatedDeclarations = [...accordionDeclarations, values];
    return handleSave(updatedDeclarations);
  };

  const handleShowNewForm = () => {
    setShowNewForm(true);
    setNewDeclaration(undefined);
  };

  const handleDelete = async (declarationToDelete: PrivacyDeclaration) => {
    const updatedDeclarations = system.privacy_declarations.filter(
      (dec) =>
        dec.name !== declarationToDelete.name ||
        dec.data_use !== declarationToDelete.data_use
    );
    return handleSave(updatedDeclarations, true);
  };

  const handleDeleteNew = async (declarationToDelete: PrivacyDeclaration) => {
    const success = await handleDelete(declarationToDelete);
    if (success) {
      setShowNewForm(false);
      setNewDeclaration(undefined);
    }
    return success;
  };

  const showAddDataUseButton =
    system.privacy_declarations.length > 0 ||
    (system.privacy_declarations.length === 0 && !showNewForm);

  return (
    <Stack spacing={3}>
      <PrivacyDeclarationAccordion
        privacyDeclarations={accordionDeclarations}
        onEdit={handleEditDeclaration}
        onDelete={handleDelete}
        {...dataProps}
      />
      {showNewForm ? (
        <Box backgroundColor="gray.50" p={6} data-testid="new-declaration-form">
          <PrivacyDeclarationForm
            initialValues={newDeclaration}
            onSubmit={saveNewDeclaration}
            onDelete={handleDeleteNew}
            {...dataProps}
          />
        </Box>
      ) : null}
      {showAddDataUseButton ? (
        <Box py={2}>
          <Tooltip
            label="Add another use case"
            hasArrow
            placement="top"
            isDisabled={accordionDeclarations.length === 0}
          >
            <Button
              colorScheme="primary"
              size="xs"
              data-testid="add-btn"
              onClick={handleShowNewForm}
              disabled={showNewForm && !newDeclaration}
            >
              Add a Data Use +
            </Button>
          </Tooltip>
        </Box>
      ) : null}
    </Stack>
  );
};

export default PrivacyDeclarationManager;
