import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { Box, Stack, Text, useToast } from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useUpdateSystemMutation } from "~/features/system/system.slice";
import {
  PrivacyDeclarationResponse,
  System,
  SystemResponse,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";
import { DataProps, PrivacyDeclarationForm } from "./PrivacyDeclarationForm";

interface Props {
  system: SystemResponse;
  includeCustomFields?: boolean;
  includeCookies?: boolean;
  onSave?: (system: System) => void;
}

const PrivacyDeclarationManager = ({
  system,
  includeCustomFields,
  includeCookies,
  onSave,
  ...dataProps
}: Props & DataProps) => {
  const toast = useToast();

  const [updateSystemMutationTrigger] = useUpdateSystemMutation();
  const [showNewForm, setShowNewForm] = useState(false);
  const [newDeclaration, setNewDeclaration] = useState<
    PrivacyDeclarationResponse | undefined
  >(undefined);

  // Accordion declarations include all declarations but the newly created one (if it exists)
  const accordionDeclarations = useMemo(() => {
    if (!newDeclaration) {
      return system.privacy_declarations;
    }

    return system.privacy_declarations.filter(
      (pd) => pd.id !== newDeclaration.id,
    );
  }, [newDeclaration, system]);

  const checkAlreadyExists = (values: PrivacyDeclarationResponse) => {
    if (
      accordionDeclarations.filter(
        (d) => d.data_use === values.data_use && d.name === values.name,
      ).length > 0
    ) {
      toast(
        errorToastParams(
          "A declaration already exists with that data use in this system. Please supply a different data use.",
        ),
      );
      return true;
    }
    return false;
  };

  const handleSave = async (
    updatedDeclarations: PrivacyDeclarationResponse[],
    isDelete?: boolean,
  ) => {
    // The API can return a null name, but cannot receive a null name,
    // so do an additional transform here (fides#3862)
    const transformedDeclarations = updatedDeclarations.map((d) => ({
      ...d,
      name: d.name ?? "",
    }));
    const systemBodyWithDeclaration = {
      ...system,
      privacy_declarations: transformedDeclarations,
    };
    const handleResult = (
      result:
        | { data: SystemResponse }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while updating the system. Please try again.",
        );

        toast(errorToastParams(errorMsg));
        return undefined;
      }
      toast.closeAll();
      toast(
        successToastParams(isDelete ? "Data use deleted" : "Data use saved"),
      );
      if (onSave) {
        onSave(result.data);
      }
      return result.data.privacy_declarations;
    };

    const updateSystemResult = await updateSystemMutationTrigger(
      systemBodyWithDeclaration,
    );

    return handleResult(updateSystemResult);
  };

  const handleEditDeclaration = async (
    oldDeclaration: PrivacyDeclarationResponse,
    updatedDeclaration: PrivacyDeclarationResponse,
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
    const updatedDeclarations = system.privacy_declarations.map((dec) =>
      dec.id === oldDeclaration.id ? updatedDeclaration : dec,
    );
    return handleSave(updatedDeclarations);
  };

  const saveNewDeclaration = async (values: PrivacyDeclarationResponse) => {
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
          pd.data_use === values.data_use,
      )[0];
      setNewDeclaration(savedDeclaration);
    }
    return res;
  };

  const handleDelete = async (
    declarationToDelete: PrivacyDeclarationResponse,
  ) => {
    const updatedDeclarations = system.privacy_declarations.filter(
      (dec) => dec.id !== declarationToDelete.id,
    );
    return handleSave(updatedDeclarations, true);
  };

  const handleDeleteNew = async (
    declarationToDelete: PrivacyDeclarationResponse,
  ) => {
    const success = await handleDelete(declarationToDelete);
    if (success) {
      setShowNewForm(false);
      setNewDeclaration(undefined);
    }
    return success;
  };

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
        includeCookies={includeCookies}
        {...dataProps}
      />
      {showNewForm ? (
        <Box backgroundColor="gray.50" p={4} data-testid="new-declaration-form">
          <PrivacyDeclarationForm
            initialValues={newDeclaration}
            onSubmit={saveNewDeclaration}
            onDelete={handleDeleteNew}
            includeCustomFields={includeCustomFields}
            includeCookies={includeCookies}
            {...dataProps}
          />
        </Box>
      ) : null}
      {system.privacy_declarations.length === 0 ? (
        <Text fontSize="sm" lineHeight={5} fontWeight="medium" pl={2}>
          No data uses
        </Text>
      ) : null}
    </Stack>
  );
};

export default PrivacyDeclarationManager;
