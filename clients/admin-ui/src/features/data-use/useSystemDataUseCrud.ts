import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import { useToast } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useUpdateSystemMutation } from "~/features/system";
import {
  PrivacyDeclaration,
  PrivacyDeclarationResponse,
  SystemResponse,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

const useSystemDataUseCrud = (system: SystemResponse) => {
  const toast = useToast();
  const [updateSystem] = useUpdateSystemMutation();

  const declarationAlreadyExists = (values: PrivacyDeclaration) => {
    if (
      !!system.privacy_declarations.find(
        (d) => d.data_use === values.data_use && d.name === values.name,
      )
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

  const handleResult = (
    result:
      | { data: SystemResponse }
      | { error: FetchBaseQueryError | SerializedError },
    isDelete?: boolean,
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
    toast(successToastParams(isDelete ? "Data use deleted" : "Data use saved"));
    return result.data.privacy_declarations;
  };

  const patchDataUses = async (
    updatedDeclarations: Omit<PrivacyDeclarationResponse, "id">[],
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

    const updateSystemResult = await updateSystem(systemBodyWithDeclaration);

    return handleResult(updateSystemResult, isDelete);
  };

  const createDataUse = async (values: PrivacyDeclaration) => {
    if (declarationAlreadyExists(values)) {
      return undefined;
    }

    toast.closeAll();
    const updatedDeclarations = [...system.privacy_declarations, values];
    return patchDataUses(updatedDeclarations);
  };

  const updateDataUse = async (
    oldDeclaration: PrivacyDeclarationResponse,
    updatedDeclaration: PrivacyDeclarationResponse,
  ) => {
    // Do not allow editing a privacy declaration to have the same data use as one that already exists
    if (
      updatedDeclaration.id !== oldDeclaration.id &&
      declarationAlreadyExists(updatedDeclaration)
    ) {
      return undefined;
    }
    // Because the data use can change, we also need a reference to the old declaration in order to
    // make sure we are replacing the proper one
    const updatedDeclarations = system.privacy_declarations.map((dec) =>
      dec.id === oldDeclaration.id ? updatedDeclaration : dec,
    );
    return patchDataUses(updatedDeclarations);
  };

  const deleteDataUse = async (
    declarationToDelete: PrivacyDeclarationResponse,
  ) => {
    const updatedDeclarations = system.privacy_declarations.filter(
      (dec) => dec.id !== declarationToDelete.id,
    );
    return patchDataUses(updatedDeclarations, true);
  };

  const deleteDeclarationByDataUse = async (use: string) => {
    const updatedDeclarations = system.privacy_declarations.filter(
      (dec) => dec.data_use !== use,
    );
    return patchDataUses(updatedDeclarations, true);
  };

  return {
    createDataUse,
    updateDataUse,
    deleteDataUse,
    deleteDeclarationByDataUse,
  };
};

export default useSystemDataUseCrud;
