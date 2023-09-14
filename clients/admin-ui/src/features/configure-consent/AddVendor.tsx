import {
  Box,
  Button,
  ButtonGroup,
  useDisclosure,
  useToast,
  VStack,
} from "@fidesui/react";
import { FieldArray, Form, Formik, FormikHelpers } from "formik";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import {
  selectAllDictEntries,
  useGetAllDictionaryEntriesQuery,
} from "~/features/plus/plus.slice";
import { useCreateSystemMutation } from "~/features/system";
import { PrivacyDeclaration } from "~/types/api";

import { getErrorMessage, isErrorResult } from "../common/helpers";
import { errorToastParams, successToastParams } from "../common/toast";
import AddModal from "./AddModal";
import DataUseBlock from "./DataUseBlock";

interface MinimalPrivacyDeclaration {
  name: string;
  data_use: PrivacyDeclaration["data_use"];
  data_categories: PrivacyDeclaration["data_categories"];
  cookies: string[];
}

interface FormValues {
  name: string;
  vendor_id?: number;
  privacy_declarations: MinimalPrivacyDeclaration[];
}

const EMPTY_DECLARATION: MinimalPrivacyDeclaration = {
  name: "",
  data_use: "",
  data_categories: ["user"],
  cookies: [],
};

const initialValues: FormValues = {
  name: "",
  vendor_id: undefined,
  // TODO(fides#4059): data categories will eventually be optional
  privacy_declarations: [EMPTY_DECLARATION],
};

const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Vendor name"),
});

const DictionaryValidationSchema = Yup.object().shape({
  vendor_id: Yup.string().required().label("Vendor"),
});

const AddVendor = () => {
  const modal = useDisclosure();
  const toast = useToast();

  // Subscribe and get dictionary values
  const features = useFeatures();
  const { dictionaryService: hasDictionary } = features;
  const { isLoading } = useGetAllDictionaryEntriesQuery(undefined, {
    skip: !hasDictionary,
  });
  const dictionaryOptions = useAppSelector(selectAllDictEntries);

  const [createSystemMutationTrigger] = useCreateSystemMutation();

  const handleSuggestions = () => {
    /* TODO */
  };

  const handleSubmit = async (
    values: FormValues,
    helpers: FormikHelpers<FormValues>
  ) => {
    const transformedDeclarations = values.privacy_declarations
      .filter((dec) => dec.data_use !== EMPTY_DECLARATION.data_use)
      .map((dec) => {
        const transformedCookies = dec.cookies.map((name) => ({
          name,
          path: "/",
        }));
        return { ...dec, cookies: transformedCookies };
      });
    const payload = {
      ...values,
      fides_key: formatKey(values.name),
      system_type: "",
      privacy_declarations: transformedDeclarations,
    };
    const result = await createSystemMutationTrigger(payload);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }
    toast(successToastParams("Vendor successfully added!"));
    helpers.resetForm();
    modal.onClose();
  };

  const validationSchema = hasDictionary
    ? DictionaryValidationSchema
    : ValidationSchema;

  return (
    <>
      <Button onClick={modal.onOpen} data-testid="add-vendor-btn">
        Add vendor
      </Button>
      <Formik
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        validationSchema={validationSchema}
      >
        {({ dirty, values, isValid, errors }) => (
          <AddModal
            isOpen={modal.isOpen}
            onClose={modal.onClose}
            title="Add a vendor"
            onSuggestionClick={handleSuggestions}
            suggestionsDisabled={values.vendor_id == null}
          >
            <Box data-testid="add-vendor-modal-content">
              <Form>
                <VStack alignItems="start">
                  {hasDictionary ? (
                    <CustomSelect
                      id="vendor"
                      name="vendor_id"
                      label="Vendor"
                      placeholder="Select a vendor"
                      singleValueBlock
                      options={dictionaryOptions}
                      tooltip="Select the vendor that matches the system"
                      isCustomOption
                      variant="stacked"
                      isRequired
                    />
                  ) : (
                    <CustomTextInput
                      id="name"
                      name="name"
                      isRequired
                      label="Vendor name"
                      tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                      variant="stacked"
                    />
                  )}
                  <FieldArray
                    name="privacy_declarations"
                    render={(arrayHelpers) => {
                      console.log({ values, dirty, isValid, errors });
                      return (
                        <>
                          {values.privacy_declarations.map(
                            (declaration, idx) => (
                              <DataUseBlock
                                key={declaration.data_use || idx}
                                index={idx}
                              />
                            )
                          )}
                          <Button
                            size="xs"
                            variant="ghost"
                            colorScheme="complimentary"
                            onClick={() => {
                              arrayHelpers.push(EMPTY_DECLARATION);
                            }}
                            disabled={
                              values.privacy_declarations[
                                values.privacy_declarations.length - 1
                              ].data_use === EMPTY_DECLARATION.data_use
                            }
                          >
                            Add data use +
                          </Button>
                        </>
                      );
                    }}
                  />
                  <ButtonGroup
                    size="sm"
                    width="100%"
                    justifyContent="space-between"
                  >
                    <Button variant="outline">Cancel</Button>
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
        )}
      </Formik>
    </>
  );
};

export default AddVendor;
