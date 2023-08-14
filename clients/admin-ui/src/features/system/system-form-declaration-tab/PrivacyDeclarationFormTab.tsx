import {
  Box,
  Button,
  ButtonProps,
  DeleteIcon,
  Divider,
  Heading,
  HStack,
  IconButton,
  Stack,
  Text,
  Tooltip,
  useToast,
  WarningTwoIcon,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import PrivacyDeclarationAccordion from "~/features/system/privacy-declarations/PrivacyDeclarationAccordion";
import { useUpdateSystemMutation } from "~/features/system/system.slice";
import PrivacyDeclarationDisplayGroup from "~/features/system/system-form-declaration-tab/PrivacyDeclarationDisplayGroup";
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

import { MockDeclarationsData } from "../MockSystemData";
import { NewDeclaration, NewSystem } from "../newSystemMockType";

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

  const checkAlreadyExists = (values: PrivacyDeclarationResponse) => 
    // if (
    //   system.privacy_declarations.filter(
    //     (d) => d.data_use === values.data_use && d.name === values.name
    //   ).length > 0
    // ) {
    //   toast(
    //     errorToastParams(
    //       "A declaration already exists with that data use in this system. Please supply a different data use."
    //     )
    //   );
    //   return true;
    // }
     false
  ;

  const handleSave = async (
    updatedDeclarations: PrivacyDeclarationResponse[],
    isDelete?: boolean
  ) => {
    console.log("saving declarations...");
    console.log(updatedDeclarations);
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

  const saveNewDeclaration = async (values: PrivacyDeclarationResponse) => {
    if (checkAlreadyExists(values)) {
      return undefined;
    }

    toast.closeAll();
    const updatedDeclarations = [...system.privacy_declarations, values];
    const res = await handleSave(updatedDeclarations);
    if (res) {
      const savedDeclaration = res.filter(
        (pd) =>
          (pd.name ? pd.name === values.name : true) &&
          pd.data_use === values.data_use
      )[0];
    }
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

  const handleCloseForm = () => {
    setShowForm(false);
    setCurrentDeclaration(undefined);
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
    <Stack spacing={3}>
      {MockDeclarationsData.length === 0 ? (
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
                You don't have a data use set up for this system yet.
              </Heading>
              <Text size="sm">[copy]</Text>
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
          declarations={MockDeclarationsData}
          handleAdd={handleOpenNewForm}
          handleEdit={handleOpenEditForm}
          handleDelete={handleDelete}
        />
      )}
      <PrivacyDeclarationFormModal isOpen={showForm} onClose={handleCloseForm}>
        <PrivacyDeclarationForm
          initialValues={currentDeclaration}
          onSubmit={saveNewDeclaration}
          onCancel={handleCloseForm}
          includeCustomFields={includeCustomFields}
          includeCookies={includeCookies}
          {...dataProps}
        />
      </PrivacyDeclarationFormModal>
    </Stack>
  );
};

export default PrivacyDeclarationFormTab;
