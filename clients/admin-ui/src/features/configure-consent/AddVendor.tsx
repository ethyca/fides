import {
  Box,
  Button,
  ButtonGroup,
  ButtonProps,
  useDisclosure,
  useToast,
  VStack,
} from "@fidesui/react";
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
import { selectAllSystems, useCreateSystemMutation } from "~/features/system";
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
import { errorToastParams, successToastParams } from "../common/toast";
import AddModal from "./AddModal";
import { EMPTY_DECLARATION, FormValues } from "./constants";
import DataUsesForm from "./DataUsesForm";

const defaultInitialValues: FormValues = {
  name: "",
  vendor_id: undefined,
  privacy_declarations: [EMPTY_DECLARATION],
};

type ButtonVariant = "primary" | "outline";

const AddVendor = ({
  buttonLabel,
  buttonVariant = "primary",
  onButtonClick,
}: {
  buttonLabel?: string;
  buttonVariant?: ButtonVariant;
  onButtonClick?: () => void;
}) => {
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const dispatch = useAppDispatch();

  const systems = useAppSelector(selectAllSystems);

  const ValidationSchema = useMemo(
    () =>
      Yup.object().shape({
        name: Yup.string()
          .required()
          .label("Vendor name")
          .test("is-unique", "", (value, context) => {
            const takenSystemNames = systems.map((s) => s.name);
            if (takenSystemNames.some((name) => name === value)) {
              return context.createError({
                message: `You already have a vendor called "${value}". Please specify a unique name for this vendor.`,
              });
            }
            return true;
          }),
      }),
    [systems]
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

  const handleVendorSelected = (vendorId?: string) => {
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

  const openButtonStyles: ButtonProps =
    buttonVariant === "primary"
      ? {
          size: "sm",
          colorScheme: "primary",
        }
      : {
          size: "xs",
          variant: "outline",
        };

  return (
    <>
      <Button
        onClick={handleOpenButtonClicked}
        data-testid="add-vendor-btn"
        {...openButtonStyles}
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
          <AddModal
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
        )}
      </Formik>
    </>
  );
};

export default AddVendor;
