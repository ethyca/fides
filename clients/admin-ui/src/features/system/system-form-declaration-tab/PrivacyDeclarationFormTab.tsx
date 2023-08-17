import {
  Box,
  Button,
  ButtonProps,
  Divider,
  Heading,
  HStack,
  Stack,
  Text,
  useToast,
  WarningTwoIcon,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { useEffect, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useUpdateSystemMutation } from "~/features/system/system.slice";
import {
  PrivacyDeclarationDisplayGroup,
  PrivacyDeclarationTabTable,
} from "~/features/system/system-form-declaration-tab/PrivacyDeclarationDisplayGroup";
import {
  DataProps,
  PrivacyDeclarationForm,
} from "~/features/system/system-form-declaration-tab/PrivacyDeclarationForm";
import { PrivacyDeclarationFormModal } from "~/features/system/system-form-declaration-tab/PrivacyDeclarationFormModal";
import {
  PrivacyDeclarationResponse,
  System,
  SystemResponse,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

interface Props {
  system: SystemResponse;
  addButtonProps?: ButtonProps;
  includeCustomFields?: boolean;
  includeCookies?: boolean;
  onSave?: (system: System) => void;
}

const PrivacyDeclarationFormTab = ({
  system,
  addButtonProps,
  includeCustomFields,
  includeCookies,
  onSave,
  ...dataProps
}: Props & DataProps) => {
  const toast = useToast();

  const [updateSystemMutationTrigger] = useUpdateSystemMutation();
  const [showForm, setShowForm] = useState(false);
  const [currentDeclaration, setCurrentDeclaration] = useState<
    PrivacyDeclarationResponse | undefined
  >(undefined);

  const assignedCookies = [
    ...system.privacy_declarations
      .filter((d) => d.cookies !== undefined)
      .flatMap((d) => d.cookies),
  ];

  const unassignedCookies = system.cookies
    ? system.cookies.filter((c) => !assignedCookies.includes(c))
    : undefined;

  const checkAlreadyExists = (values: PrivacyDeclarationResponse) => {
    if (
      system.privacy_declarations.filter(
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
    updatedDeclarations: PrivacyDeclarationResponse[],
    isDelete?: boolean
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
      return result.data.privacy_declarations;
    };

    const updateSystemResult = await updateSystemMutationTrigger(
      systemBodyWithDeclaration
    );

    return handleResult(updateSystemResult);
  };

  const handleEditDeclaration = async (
    oldDeclaration: PrivacyDeclarationResponse,
    updatedDeclaration: PrivacyDeclarationResponse
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
      dec.id === oldDeclaration.id ? updatedDeclaration : dec
    );
    return handleSave(updatedDeclarations);
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setCurrentDeclaration(undefined);
  };

  const handleCreateDeclaration = async (
    values: PrivacyDeclarationResponse
  ) => {
    if (checkAlreadyExists(values)) {
      return undefined;
    }

    toast.closeAll();
    const updatedDeclarations = [...system.privacy_declarations, values];
    const res = await handleSave(updatedDeclarations);

    handleCloseForm();
    return res;
  };

  const handleOpenNewForm = () => {
    setShowForm(true);
    setCurrentDeclaration(undefined);
  };

  const handleOpenEditForm = (
    declarationToEdit: PrivacyDeclarationResponse
  ) => {
    setShowForm(true);
    setCurrentDeclaration(declarationToEdit);
  };

  const handleSubmit = (values: PrivacyDeclarationResponse) => {
    handleCloseForm();
    if (currentDeclaration) {
      handleEditDeclaration(currentDeclaration, values);
    } else {
      handleCreateDeclaration(values);
    }
  };

  const handleDelete = async (
    declarationToDelete: PrivacyDeclarationResponse
  ) => {
    const updatedDeclarations = system.privacy_declarations.filter(
      (dec) => dec.id !== declarationToDelete.id
    );
    return handleSave(updatedDeclarations, true);
  };

  // Reset the new form when the system changes (i.e. when clicking on a new datamap node)
  useEffect(() => {
    setShowForm(false);
  }, [system.fides_key]);

  return (
    <Stack spacing={6}>
      {system.privacy_declarations.length === 0 ? (
        <Box
          display="flex"
          flexDirection="row"
          p={4}
          mt={6}
          border="1px"
          borderColor="blue.400"
          borderRadius={8}
          backgroundColor="gray.50"
        >
          <HStack spacing={2} display="flex" alignItems="start">
            <WarningTwoIcon color="blue.400" boxSize="18px" />
            <Stack spacing={1}>
              <Heading as="h4" size="md">
                You don&apos;t have a data use set up for this system yet.
              </Heading>
              <Text size="sm">
                A Data Use is the purpose for which data is used in a system. In
                Fides, a system may have more than one Data Use. For example, a
                CRM system may be used both for "Customer Support" and also for
                "Email Marketing", each of these is a Data Use.
              </Text>
              <HStack>
                <Button
                  variant="outline"
                  size="md"
                  data-testid="add-btn"
                  onClick={handleOpenNewForm}
                  mt={2}
                  {...addButtonProps}
                >
                  Add data use
                </Button>
              </HStack>
            </Stack>
          </HStack>
        </Box>
      ) : (
        <PrivacyDeclarationDisplayGroup
          heading="Data use"
          declarations={system.privacy_declarations}
          handleAdd={handleOpenNewForm}
          handleEdit={handleOpenEditForm}
          handleDelete={handleDelete}
        />
      )}
      {unassignedCookies && unassignedCookies.length > 0 ? (
        <PrivacyDeclarationTabTable heading="Unassigned cookies">
          {unassignedCookies.map((cookie) => (
            <>
              <Box px={6} py={4}>
                <Text>{cookie.name}</Text>
              </Box>
              <Divider />
            </>
          ))}
        </PrivacyDeclarationTabTable>
      ) : null}
      <PrivacyDeclarationFormModal isOpen={showForm} onClose={handleCloseForm}>
        <PrivacyDeclarationForm
          initialValues={currentDeclaration}
          onSubmit={handleSubmit}
          onCancel={handleCloseForm}
          {...dataProps}
        />
      </PrivacyDeclarationFormModal>
    </Stack>
  );
};

export default PrivacyDeclarationFormTab;
