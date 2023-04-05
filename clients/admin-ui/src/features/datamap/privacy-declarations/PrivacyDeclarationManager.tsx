import { Box, Button, Stack, Tooltip, useToast } from "@fidesui/react";
import { useEffect, useMemo, useState } from "react";

import { PrivacyDeclarationWithId } from "~/features/datamap/privacy-declarations/types";
import { PrivacyDeclaration, System } from "~/types/api";

import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";
import {
  DataProps,
  PrivacyDeclarationForm,
  transformPrivacyDeclarationsToHaveId,
} from "./PrivacyDeclarationForm";

const transformDeclarationForSubmission = (
  formValues: PrivacyDeclarationWithId
): PrivacyDeclaration => {
  // Remove the id which is only a frontend artifact
  const { id, ...values } = formValues;
  return {
    ...values,
    // Fill in an empty string for name because of https://github.com/ethyca/fideslang/issues/98
    name: values.name ?? "",
  };
};

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
    PrivacyDeclarationWithId | undefined
  >(undefined);

  const accordionDeclarations = useMemo(() => {
    const declarations = transformPrivacyDeclarationsToHaveId(
      system.privacy_declarations
    );
    if (!newDeclaration) {
      return declarations;
    }
    return declarations.filter((pd) => pd.id !== newDeclaration.id);
  }, [newDeclaration, system]);

  const checkAlreadyExists = (values: PrivacyDeclaration) => {
    if (
      accordionDeclarations.filter(
        (d) => d.data_use === values.data_use && d.name === values.name
      ).length > 0
    ) {
      onCollision();
      return true;
    }
    return false;
  };

  const handleSave = async (
    updatedDeclarations: PrivacyDeclarationWithId[],
    isDelete?: boolean
  ) => {
    const transformedDeclarations = updatedDeclarations.map((d) =>
      transformDeclarationForSubmission(d)
    );
    const success = await onSave(transformedDeclarations, isDelete);
    return success;
  };

  const handleEditDeclaration = async (
    oldDeclaration: PrivacyDeclarationWithId,
    updatedDeclaration: PrivacyDeclarationWithId
  ) => {
    // Do not allow editing a privacy declaration to have the same data use as one that already exists
    if (
      updatedDeclaration.id !== oldDeclaration.id &&
      checkAlreadyExists(updatedDeclaration)
    ) {
      return false;
    }
    // Because the data use can change, we also need a reference to the old declaration in order to
    // make sure we are replacing the proper one
    const updatedDeclarations = accordionDeclarations.map((dec) =>
      dec.id === oldDeclaration.id ? updatedDeclaration : dec
    );
    return handleSave(updatedDeclarations);
  };

  const saveNewDeclaration = async (values: PrivacyDeclarationWithId) => {
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

  const handleDelete = async (
    declarationToDelete: PrivacyDeclarationWithId
  ) => {
    const updatedDeclarations = transformPrivacyDeclarationsToHaveId(
      system.privacy_declarations
    ).filter((dec) => dec.id !== declarationToDelete.id);
    return handleSave(updatedDeclarations, true);
  };

  const handleDeleteNew = async (
    declarationToDelete: PrivacyDeclarationWithId
  ) => {
    const success = await handleDelete(declarationToDelete);
    if (success) {
      setShowNewForm(false);
      setNewDeclaration(undefined);
    }
    return success;
  };

  useEffect(() => {
    setShowNewForm(false);
  }, [system.fides_key]);

  const showAddDataUseButton =
    system.privacy_declarations.length > 0 ||
    (system.privacy_declarations.length === 0 && !showNewForm);

  return (
    <Stack spacing={0} mb={4}>
      <PrivacyDeclarationAccordion
        privacyDeclarations={accordionDeclarations}
        onEdit={handleEditDeclaration}
        onDelete={handleDelete}
        {...dataProps}
      />
      {showNewForm ? (
        <Box
          backgroundColor="gray.50"
          padding={4}
          paddingTop={0}
          data-testid="new-declaration-form"
        >
          <PrivacyDeclarationForm
            initialValues={newDeclaration}
            onSubmit={saveNewDeclaration}
            onDelete={handleDeleteNew}
            {...dataProps}
          />
        </Box>
      ) : null}
      {showAddDataUseButton ? (
        <Box
          backgroundColor="gray.50"
          m={0}
          p={4}
          data-testid="new-declaration-button"
        >
          <Tooltip
            label="Add a Data Use"
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
