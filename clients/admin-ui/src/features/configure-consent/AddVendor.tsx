import {
  AntButton as Button,
  AntButtonProps as ButtonProps,
  Box,
  useDisclosure,
  useToast,
  VStack,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import { useMemo, useRef } from "react";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { CustomTextInput } from "~/features/common/form/inputs";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import {
  selectAllDictEntries,
  selectDictEntry,
  useGetAllDictionaryEntriesQuery,
} from "~/features/plus/plus.slice";
import {
  useCreateSystemMutation,
  useLazyGetSystemsQuery,
} from "~/features/system";
import {
  selectLockedForGVL,
  selectSuggestions,
  setLockedForGVL,
  setSuggestions,
} from "~/features/system/dictionary-form/dict-suggestion.slice";
import GVLNotice from "~/features/system/GVLNotice";
import VendorSelector from "~/features/system/VendorSelector";
import { System } from "~/types/api";

import {
  extractVendorSource,
  getErrorMessage,
  isErrorResult,
  VendorSources,
} from "../common/helpers";
import FormModal from "../common/modals/FormModal";
import { errorToastParams, successToastParams } from "../common/toast";
import { EMPTY_DECLARATION, FormValues } from "./constants";
import DataUsesForm from "./DataUsesForm";

const defaultInitialValues: FormValues = {
  name: "",
  vendor_id: undefined,
  privacy_declarations: [EMPTY_DECLARATION],
};

const AddVendor = ({
  buttonLabel,
  onButtonClick,
  buttonProps,
}: {
  buttonLabel?: string;
  onButtonClick?: () => void;
  buttonProps?: ButtonProps;
}) => {
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const dispatch = useAppDispatch();

  const [getSystemQueryTrigger] = useLazyGetSystemsQuery();

  const ValidationSchema = useMemo(
    () =>
      Yup.object().shape({
        name: Yup.string()
          .required()
          .label("Vendor name")
          .test("is-unique", "", async (value, context) => {
            const { data } = await getSystemQueryTrigger({
              page: 1,
              size: 10,
              search: value,
            });
            const similarSystemNames = data?.items || [];
            if (similarSystemNames.some((s) => s.name === value)) {
              return context.createError({
                message: `You already have a vendor called "${value}". Please specify a unique name for this vendor.`,
              });
            }
            return true;
          }),
      }),
    [getSystemQueryTrigger],
  );

  // Subscribe and get dictionary values
  const { tcf, dictionaryService } = useFeatures();
  const { isLoading } = useGetAllDictionaryEntriesQuery(undefined, {
    skip: !dictionaryService,
  });
  const dictionaryOptions = useAppSelector(selectAllDictEntries);
  const lockedForGVL = useAppSelector(selectLockedForGVL);

  const [createSystemMutationTrigger] = useCreateSystemMutation();
  const suggestionsState = useAppSelector(selectSuggestions);

  const handleCloseModal = () => {
    onClose();
    dispatch(setSuggestions("initial"));
    dispatch(setLockedForGVL(false));
  };

  const formRef = useRef(null);
  const selectedVendorId = formRef.current
    ? // @ts-ignore
      formRef.current.values.vendor_id
    : undefined;
  const dictEntry = useAppSelector(selectDictEntry(selectedVendorId || ""));

  const handleSubmit = async (
    values: FormValues,
    helpers: FormikHelpers<FormValues>,
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

    const payload = {
      ...dictEntry,
      ...values,
      fides_key: formatKey(values.name),
      system_type: "",
      privacy_declarations: transformedDeclarations,
    } as System;

    const result = await createSystemMutationTrigger(payload);

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }
    toast(successToastParams("Vendor successfully created!"));
    helpers.resetForm();
    handleCloseModal();
  };

  const handleVendorSelected = (vendorId?: string | null) => {
    if (!dictionaryService) {
      return;
    }
    if (!vendorId) {
      dispatch(setSuggestions("hiding"));
      dispatch(setLockedForGVL(false));
      return;
    }
    dispatch(setSuggestions("showing"));
    if (tcf && extractVendorSource(vendorId) === VendorSources.GVL) {
      dispatch(setLockedForGVL(true));
    } else {
      dispatch(setLockedForGVL(false));
    }
  };

  const handleOpenButtonClicked = () => {
    if (onButtonClick) {
      onButtonClick();
    } else {
      onOpen();
    }
  };

  return (
    <>
      <Button
        onClick={handleOpenButtonClicked}
        data-testid="add-vendor-btn"
        {...buttonProps}
      >
        {buttonLabel}
      </Button>
      <Formik
        initialValues={defaultInitialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        validationSchema={ValidationSchema}
        innerRef={formRef}
      >
        {({ dirty, isValid, resetForm }) => (
          <FormModal
            isOpen={isOpen}
            onClose={handleCloseModal}
            title="Add a vendor"
          >
            <Box data-testid="add-vendor-modal-content" my={4}>
              {lockedForGVL ? <GVLNotice /> : null}
              <Form>
                <VStack alignItems="start" spacing={6}>
                  {dictionaryService ? (
                    <VendorSelector
                      label="Vendor name"
                      options={dictionaryOptions}
                      onVendorSelected={handleVendorSelected}
                      isCreate
                      lockedForGVL={lockedForGVL}
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
                  <DataUsesForm
                    showSuggestions={suggestionsState === "showing"}
                    isCreate
                    disabled={lockedForGVL}
                  />
                  <div className="flex w-full justify-between">
                    <Button
                      onClick={() => {
                        handleCloseModal();
                        resetForm();
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="primary"
                      htmlType="submit"
                      disabled={isLoading || !dirty || !isValid}
                      loading={isLoading}
                      data-testid="save-btn"
                    >
                      Save vendor
                    </Button>
                  </div>
                </VStack>
              </Form>
            </Box>
          </FormModal>
        )}
      </Formik>
    </>
  );
};

export default AddVendor;
