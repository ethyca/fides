import {
  Box,
  Button,
  ButtonGroup,
  useDisclosure,
  useToast,
  VStack,
} from "@fidesui/react";
import { Form, Formik, FormikHelpers } from "formik";
import { useState } from "react";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  CustomCreatableSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { dataUseIsConsentUse } from "~/features/configure-consent/vendor-transform";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import {
  selectAllDictEntries,
  useGetAllDictionaryEntriesQuery,
} from "~/features/plus/plus.slice";
import {
  useCreateSystemMutation,
  useUpdateSystemMutation,
} from "~/features/system";
import { System } from "~/types/api";

import { getErrorMessage, isErrorResult } from "../common/helpers";
import { errorToastParams, successToastParams } from "../common/toast";
import AddModal from "./AddModal";
import { AddMultipleVendors } from "./AddMultipleVendors";
import { EMPTY_DECLARATION, FormValues } from "./constants";
import DataUsesForm from "./DataUsesForm";

const defaultInitialValues: FormValues = {
  name: "",
  vendor_id: undefined,
  privacy_declarations: [EMPTY_DECLARATION],
};

const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Vendor name"),
});

const DictionaryValidationSchema = Yup.object().shape(
  {
    // to allow creation/editing of non-dictionary systems even with
    // dictionary enabled, only require one of either vendor_id or name
    vendor_id: Yup.string().when("name", {
      is: (name: string) => name === "" || null,
      then: Yup.string().required().label("Vendor"),
      otherwise: Yup.string().nullable().label("Vendor"),
    }),
    name: Yup.string().when("vendor_id", {
      is: (vendor_id: string) => vendor_id === "" || null,
      then: Yup.string().required().label("Name"),
      otherwise: Yup.string().nullable().label("Name"),
    }),
  },
  [["name", "vendor_id"]]
);

const AddVendor = ({
  passedInSystem,
  onCloseModal,
}: {
  passedInSystem?: System;
  onCloseModal?: () => void;
}) => {
  const defaultModal = useDisclosure();
  const modal = {
    ...defaultModal,
    isOpen: passedInSystem ? true : defaultModal.isOpen,
  };
  const toast = useToast();

  // Subscribe and get dictionary values
  const features = useFeatures();
  const { dictionaryService: hasDictionary } = features;
  const { isLoading } = useGetAllDictionaryEntriesQuery(undefined, {
    skip: !hasDictionary,
  });
  const dictionaryOptions = useAppSelector(selectAllDictEntries);

  const [createSystemMutationTrigger] = useCreateSystemMutation();
  const [updateSystemMutationTrigger] = useUpdateSystemMutation();
  const [isShowingSuggestions, setIsShowingSuggestions] = useState(false);

  const handleCloseModal = () => {
    modal.onClose();
    if (onCloseModal) {
      onCloseModal();
    }
    setIsShowingSuggestions(false);
  };

  const initialValues = passedInSystem
    ? {
      name: passedInSystem.name ?? "",
      vendor_id: passedInSystem.vendor_id,
      privacy_declarations: passedInSystem.privacy_declarations
        .filter((dec) => dataUseIsConsentUse(dec.data_use))
        .map((dec) => ({
          ...dec,
          name: dec.name ?? "",
          cookies: dec.cookies ?? [],
          cookieNames: dec.cookies ? dec.cookies.map((c) => c.name) : [],
          consent_use: dec.data_use.split(".")[0],
        })),
    }
    : defaultInitialValues;

  const handleSubmit = async (
    values: FormValues,
    helpers: FormikHelpers<FormValues>
  ) => {
    const transformedDeclarations = values.privacy_declarations
      .filter((dec) => dec.consent_use !== EMPTY_DECLARATION.consent_use)
      .flatMap((dec) => {
        // if a cookie from the form already exists on the declaration with full
        // information from the dictionary, use that; otherwise, make the cookie
        // name from the form into a new cookie
        const transformedCookies = dec.cookieNames.map((name) => {
          const existingCookie = dec.cookies.find((c) => c.name === name);
          return existingCookie ?? { name, path: "/" };
        });
        // eslint-disable-next-line @typescript-eslint/naming-convention
        const { cookieNames, consent_use, ...rest } = dec;

        // for "marketing", we create two data uses on the backend
        if (dec.consent_use === "marketing" && !dec.data_use) {
          return [
            "marketing.advertising.first_party.targeted",
            "marketing.advertising.third_party.targeted",
          ].map((dataUse) => ({
            ...rest,
            data_use: dataUse,
            cookies: transformedCookies,
          }));
        }
        return {
          ...rest,
          data_use: dec.data_use ? dec.data_use : dec.consent_use!,
          cookies: transformedCookies,
        };
      });
    // if editing and the system has existing data uses not shown on form
    // due to not being consent uses, include those in the payload
    const existingDeclarations = passedInSystem
      ? passedInSystem.privacy_declarations.filter(
        (du) => !dataUseIsConsentUse(du.data_use)
      )
      : [];
    const declarationsToSave = passedInSystem
      ? [...existingDeclarations, ...transformedDeclarations]
      : transformedDeclarations;

    // We use vendor_id to potentially store a new system name
    // so now we need to clear out vendor_id if it's not a system in the dictionary
    const vendor = dictionaryOptions.find((o) => o.value === values.vendor_id);
    const vendorId = vendor ? vendor.value : undefined;
    let { name: newName } = values;
    if (vendor) {
      newName = vendor.label;
    } else if (values.vendor_id) {
      // This is the case where the user created their own vendor name
      newName = values.vendor_id;
    }

    const payload = {
      vendor_id: vendorId,
      name: passedInSystem ? passedInSystem.name : newName,
      fides_key: passedInSystem ? passedInSystem.fides_key : formatKey(newName),
      system_type: passedInSystem ? passedInSystem.system_type : "",
      privacy_declarations: declarationsToSave,
    };

    const result = passedInSystem
      ? await updateSystemMutationTrigger(payload)
      : await createSystemMutationTrigger(payload);

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }
    toast(
      successToastParams(
        `Vendor successfully ${passedInSystem ? "updated" : "created"}!`
      )
    );
    helpers.resetForm();
    handleCloseModal();
  };

  const validationSchema = hasDictionary
    ? DictionaryValidationSchema
    : ValidationSchema;

  return (
    <>
      <Box mr={2}>
        <AddMultipleVendors onCancel={modal.onOpen} />
      </Box>
      <Formik
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        validationSchema={validationSchema}
      >
        {({ dirty, values, isValid, resetForm }) => {
          let suggestionsState;
          if (
            dictionaryOptions.every((opt) => opt.value !== values.vendor_id)
          ) {
            suggestionsState = "disabled" as const;
          } else if (isShowingSuggestions) {
            suggestionsState = "showing" as const;
          }
          return (
            <AddModal
              isOpen={modal.isOpen}
              onClose={modal.onClose}
              title={passedInSystem ? "Edit vendor" : "Add a vendor"}
              onSuggestionClick={() => {
                setIsShowingSuggestions(true);
              }}
              suggestionsState={suggestionsState}
            >
              <Box data-testid="add-vendor-modal-content" my={4}>
                <Form>
                  <VStack alignItems="start" spacing={6}>
                    {hasDictionary ? (
                      <CustomCreatableSelect
                        id="vendor"
                        name="vendor_id"
                        label="Vendor"
                        placeholder="Select a vendor"
                        singleValueBlock
                        options={dictionaryOptions}
                        tooltip="Select the vendor that matches the system"
                        isCustomOption
                        variant="stacked"
                        isDisabled={!!passedInSystem}
                        isRequired
                      />
                    ) : null}
                    {(passedInSystem && !passedInSystem.vendor_id) ||
                      !hasDictionary ? (
                      <CustomTextInput
                        id="name"
                        name="name"
                        isRequired
                        label="Vendor name"
                        tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                        variant="stacked"
                        disabled={!!passedInSystem}
                      />
                    ) : null}
                    <DataUsesForm showSuggestions={isShowingSuggestions} />
                    <ButtonGroup
                      size="sm"
                      width="100%"
                      justifyContent="space-between"
                    >
                      <Button
                        variant="outline"
                        onClick={() => {
                          handleCloseModal();
                          resetForm();
                        }}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        variant="primary"
                        isDisabled={isLoading || !dirty || !isValid}
                        isLoading={isLoading}
                        data-testid="save-btn"
                      >
                        Save vendor
                      </Button>
                    </ButtonGroup>
                  </VStack>
                </Form>
              </Box>
            </AddModal>
          );
        }}
      </Formik>
    </>
  );
};

export default AddVendor;
