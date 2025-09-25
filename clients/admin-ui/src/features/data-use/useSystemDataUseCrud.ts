import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import { useToast } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useBulkUpdateCustomFieldsMutation } from "~/features/plus/plus.slice";
import { useUpdateSystemMutation } from "~/features/system";
import {
  BulkCustomFieldRequest,
  CustomFieldWithId,
  PrivacyDeclaration,
  PrivacyDeclarationResponse,
  ResourceTypes,
  SystemResponse,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

const buildCustomFieldsPayload = (
  customFieldValues: Record<string, any>,
  resourceId: string,
): BulkCustomFieldRequest => {
  const payloadUpsert: CustomFieldWithId[] = [];
  const payloadDelete: string[] = [];
  Object.entries(customFieldValues).forEach(([id, value]) => {
    if (value) {
      payloadUpsert.push({
        id,
        value,
        resource_id: resourceId,
        custom_field_definition_id: id,
      });
    } else {
      payloadDelete.push(id);
    }
  });
  return {
    upsert: payloadUpsert,
    delete: payloadDelete,
    resource_type: ResourceTypes.PRIVACY_DECLARATION,
    resource_id: resourceId,
  };
};

const useSystemDataUseCrud = (system: SystemResponse) => {
  const toast = useToast();
  const [updateSystem] = useUpdateSystemMutation();

  const [bulkUpdateCustomFields] = useBulkUpdateCustomFieldsMutation();

  const declarationAlreadyExists = (values: PrivacyDeclaration) => {
    if (
      system.privacy_declarations.find(
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
    customFieldValues?: Record<string, any>,
    updatedDeclarationDataUse?: string,
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

    // get the ID of the modified declaration from the response and update
    // its custom fields if provided
    if (customFieldValues && updatedDeclarationDataUse) {
      const newDeclaration =
        updateSystemResult?.data?.privacy_declarations?.find(
          (d) => d.data_use === updatedDeclarationDataUse,
        );
      if (newDeclaration) {
        const customFieldsPayload = buildCustomFieldsPayload(
          customFieldValues,
          newDeclaration.id,
        );
        const bulkUpdateResult =
          await bulkUpdateCustomFields(customFieldsPayload);
        if (isErrorResult(bulkUpdateResult)) {
          const errorMsg = getErrorMessage(
            bulkUpdateResult.error,
            "An unexpected error occurred while updating custom fields for this data use. Please try again.",
          );
          toast(errorToastParams(errorMsg));
        }
      }
    }
    return handleResult(updateSystemResult, isDelete);
  };

  const createDataUse = async (
    values: PrivacyDeclaration & {
      customFieldValues?: Record<string, any>;
    },
  ) => {
    if (declarationAlreadyExists(values)) {
      return undefined;
    }

    const { customFieldValues, ...newDeclaration } = values;

    toast.closeAll();
    const updatedDeclarations = [
      ...system.privacy_declarations,
      newDeclaration,
    ];
    return patchDataUses(
      updatedDeclarations,
      false,
      customFieldValues,
      newDeclaration.data_use,
    );
  };

  const updateDataUse = async (
    oldDeclaration: PrivacyDeclarationResponse,
    values: PrivacyDeclarationResponse & {
      customFieldValues?: Record<string, any>;
    },
  ) => {
    // Do not allow editing a privacy declaration to have the same data use as one that already exists
    if (values.id !== oldDeclaration.id && declarationAlreadyExists(values)) {
      return undefined;
    }
    const { customFieldValues, ...updatedDeclaration } = values;
    // Because the data use can change, we also need a reference to the old declaration in order to
    // make sure we are replacing the proper one
    const updatedDeclarations = system.privacy_declarations.map((dec) =>
      dec.id === oldDeclaration.id ? updatedDeclaration : dec,
    );
    return patchDataUses(
      updatedDeclarations,
      false,
      customFieldValues,
      updatedDeclaration.data_use,
    );
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
