import {
  Box,
  Button,
  ButtonProps,
  Stack,
  Tooltip,
  useToast,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useUpdateSystemMutation } from "~/features/system/system.slice";
import { PrivacyDeclaration, System } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";
import {
  DataProps,
  PrivacyDeclarationForm,
  transformPrivacyDeclarationsToHaveId,
} from "./PrivacyDeclarationForm";
import { PrivacyDeclarationWithId } from "./types";

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
  addButtonProps?: ButtonProps;
  includeCustomFields?: boolean;
  onSave?: (system: System) => void;
}

const PrivacyDeclarationManager = ({
  system,
  addButtonProps,
  includeCustomFields,
  onSave,
  ...dataProps
}: Props & DataProps) => {
  const toast = useToast();

  const [updateSystemMutationTrigger] = useUpdateSystemMutation();
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
      toast(
        errorToastParams(
          "A declaration already exists with that data use in this system. Please supply a different data use."
        )
      );
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
    const systemBodyWithDeclaration = {
      ...system,
      privacy_declarations: transformedDeclarations,
    };
    const handleResult = (
      result:
        | { data: System }
        | { error: FetchBaseQueryError | SerializedError }
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while updating the system. Please try again."
        );

        toast(errorToastParams(errorMsg));
        return undefined;
      }
      toast.closeAll();
      toast(
        successToastParams(isDelete ? "Data use deleted" : "Data use saved")
      );
      if (onSave) {
        onSave(result.data);
      }
      return result.data.privacy_declarations as PrivacyDeclarationWithId[];
    };

    const updateSystemResult = await updateSystemMutationTrigger(
      systemBodyWithDeclaration
    );

    return handleResult(updateSystemResult);
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
      return undefined;
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
      return undefined;
    }

    toast.closeAll();
    const updatedDeclarations = [...accordionDeclarations, values];
    const res = await handleSave(updatedDeclarations);
    if (res) {
      const savedDeclaration = res.filter(
        (pd) =>
          (pd.name ? pd.name === values.name : true) &&
          pd.data_use === values.data_use
      )[0];
      setNewDeclaration(savedDeclaration);
    }
    return res;
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

  const showAddDataUseButton =
    system.privacy_declarations.length > 0 ||
    (system.privacy_declarations.length === 0 && !showNewForm);

  // Reset the new form when the system changes (i.e. when clicking on a new datamap node)
  useEffect(() => {
    setShowNewForm(false);
  }, [system.fides_key]);

  return (
    <Stack spacing={3}>
      <PrivacyDeclarationAccordion
        privacyDeclarations={accordionDeclarations}
        onEdit={handleEditDeclaration}
        onDelete={handleDelete}
        includeCustomFields={includeCustomFields}
        {...dataProps}
      />
      {showNewForm ? (
        <Box backgroundColor="gray.50" p={4} data-testid="new-declaration-form">
          <PrivacyDeclarationForm
            initialValues={newDeclaration}
            onSubmit={saveNewDeclaration}
            onDelete={handleDeleteNew}
            includeCustomFields={includeCustomFields}
            {...dataProps}
          />
        </Box>
      ) : null}
      {showAddDataUseButton ? (
        <Box py={2}>
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
              {...addButtonProps}
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
