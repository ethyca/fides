import {
  AntButton as Button,
  AntFlex as Flex,
  Collapse,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { isErrorResult } from "~/features/common/helpers";
import FormModal from "~/features/common/modals/FormModal";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  TCFPublisherRestrictionRequest,
  TCFRestrictionType,
  TCFVendorRestriction,
} from "~/types/api";

import {
  RESTRICTION_TYPE_LABELS,
  VENDOR_RESTRICTION_LABELS,
} from "./constants";
import {
  useCreatePublisherRestrictionMutation,
  useUpdatePublisherRestrictionMutation,
} from "./tcf-config.slice";
import { FormValues, PurposeRestriction } from "./types";
import {
  checkForVendorRestrictionConflicts,
  convertVendorIdsToRangeEntries,
  ERROR_MESSAGE,
  isValidVendorIdFormat,
} from "./validation-utils";

const IN_USE_TOOLTIP =
  "This restriction type is already in use for this purpose";

interface PurposeRestrictionFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialValues?: FormValues;
  existingRestrictions?: PurposeRestriction[];
  purposeId?: number;
  restrictionId?: string;
  configurationId: string;
}

const defaultInitialValues: FormValues = {
  restriction_type: "",
  vendor_restriction: "",
  vendor_ids: [],
};

export const PurposeRestrictionFormModal = ({
  isOpen,
  onClose,
  initialValues = defaultInitialValues,
  existingRestrictions = [],
  purposeId,
  restrictionId,
  configurationId,
}: PurposeRestrictionFormModalProps) => {
  const toast = useToast();
  const [createRestriction] = useCreatePublisherRestrictionMutation();
  const [updateRestriction] = useUpdatePublisherRestrictionMutation();

  // Get the list of restriction types that are already in use for this purpose
  const usedRestrictionTypes = existingRestrictions
    .filter((r) => r.id !== restrictionId) // Exclude current restriction when editing
    .map((r) => r.restriction_type);

  const restrictionTypeOptions = [
    {
      value: TCFRestrictionType.PURPOSE_RESTRICTION,
      label: RESTRICTION_TYPE_LABELS[TCFRestrictionType.PURPOSE_RESTRICTION],
      disabled: usedRestrictionTypes.includes(
        TCFRestrictionType.PURPOSE_RESTRICTION,
      ),
      title: usedRestrictionTypes.includes(
        TCFRestrictionType.PURPOSE_RESTRICTION,
      )
        ? IN_USE_TOOLTIP
        : undefined,
    },
    {
      value: TCFRestrictionType.REQUIRE_CONSENT,
      label: RESTRICTION_TYPE_LABELS[TCFRestrictionType.REQUIRE_CONSENT],
      disabled: usedRestrictionTypes.includes(
        TCFRestrictionType.REQUIRE_CONSENT,
      ),
      title: usedRestrictionTypes.includes(TCFRestrictionType.REQUIRE_CONSENT)
        ? IN_USE_TOOLTIP
        : undefined,
    },
    {
      value: TCFRestrictionType.REQUIRE_LEGITIMATE_INTEREST,
      label:
        RESTRICTION_TYPE_LABELS[TCFRestrictionType.REQUIRE_LEGITIMATE_INTEREST],
      disabled: usedRestrictionTypes.includes(
        TCFRestrictionType.REQUIRE_LEGITIMATE_INTEREST,
      ),
      title: usedRestrictionTypes.includes(
        TCFRestrictionType.REQUIRE_LEGITIMATE_INTEREST,
      )
        ? IN_USE_TOOLTIP
        : undefined,
    },
  ];

  const vendorRestrictionOptions = [
    {
      value: TCFVendorRestriction.RESTRICT_ALL_VENDORS,
      label:
        VENDOR_RESTRICTION_LABELS[TCFVendorRestriction.RESTRICT_ALL_VENDORS],
      disabled: existingRestrictions.length > 0,
      title:
        existingRestrictions.length > 0
          ? "Cannot restrict all vendors when other restrictions exist"
          : undefined,
    },
    {
      value: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
      label:
        VENDOR_RESTRICTION_LABELS[
          TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS
        ],
    },
    {
      value: TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS,
      label:
        VENDOR_RESTRICTION_LABELS[TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS],
    },
  ];

  // Create validation schema
  const validationSchema = Yup.object().shape({
    restriction_type: Yup.string().required("Restriction type is required"),
    vendor_restriction: Yup.string().required("Vendor restriction is required"),
    vendor_ids: Yup.array().when("vendor_restriction", {
      is: (val: string) => val !== TCFVendorRestriction.RESTRICT_ALL_VENDORS,
      then: (schema) =>
        schema
          .required("At least one vendor ID is required")
          .min(1, "At least one vendor ID is required")
          .test(
            "valid-format",
            "Vendor IDs must be numbers or ranges (e.g., 10 or 15-300)",
            (value) => value?.every((id) => isValidVendorIdFormat(id)) ?? true,
          )
          .test(
            "no-conflicts",
            ERROR_MESSAGE,
            (value, context) =>
              !checkForVendorRestrictionConflicts(
                {
                  ...context.parent,
                  vendor_ids: value,
                } as FormValues,
                existingRestrictions,
                purposeId,
                restrictionId,
              ),
          ),
    }),
  });

  const handleSubmit = async (values: FormValues): Promise<void> => {
    try {
      // Convert form values to API request format
      const request: Omit<TCFPublisherRestrictionRequest, "purpose_id"> = {
        restriction_type: values.restriction_type as TCFRestrictionType,
        vendor_restriction: values.vendor_restriction as TCFVendorRestriction,
        range_entries:
          values.vendor_restriction !==
          TCFVendorRestriction.RESTRICT_ALL_VENDORS
            ? convertVendorIdsToRangeEntries(values.vendor_ids)
            : [],
      };
      const requestWithPurposeId: TCFPublisherRestrictionRequest = {
        ...request,
        purpose_id: purposeId ?? 0,
      };

      if (restrictionId) {
        const result = await updateRestriction({
          configuration_id: configurationId,
          restriction_id: restrictionId,
          restriction: request,
        });
        if (isErrorResult(result)) {
          toast(errorToastParams("Failed to update restriction"));
          return;
        }
        toast(successToastParams("Restriction updated successfully"));
      } else {
        const result = await createRestriction({
          configuration_id: configurationId,
          restriction: requestWithPurposeId,
        });
        if (isErrorResult(result)) {
          toast(errorToastParams("Failed to create restriction"));
          return;
        }
        toast(successToastParams("Restriction created successfully"));
      }
      onClose();
    } catch (error) {
      toast(errorToastParams("Failed to save restriction"));
    }
  };

  return (
    <FormModal isOpen={isOpen} onClose={onClose} title="Edit restriction">
      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
        validationSchema={validationSchema}
      >
        {({ values, validateField, setTouched }) => (
          <Form>
            <Flex vertical className="gap-6">
              <Text className="text-sm">
                Define how specific vendors are restricted from processing data
                for this purpose. Select a restriction type, set whether the
                listed vendors are restricted or allowed, and specify which
                vendor IDs the restriction applies to.
              </Text>
              <ControlledSelect
                name="restriction_type"
                label="Restriction type"
                options={restrictionTypeOptions}
                layout="stacked"
                tooltip="Choose how vendors are permitted to process data for this purpose. This setting overrides the vendor's declared legal basis in the Global Vendor List."
                isRequired
              />
              <ControlledSelect
                name="vendor_restriction"
                label="Vendor restriction"
                options={vendorRestrictionOptions}
                layout="stacked"
                tooltip="Decide if the restriction applies to all vendors, specific vendors, or if only certain vendors are allowed."
                isRequired
              />
              <Collapse
                in={
                  !!values.restriction_type &&
                  !!values.vendor_restriction &&
                  values.vendor_restriction !==
                    TCFVendorRestriction.RESTRICT_ALL_VENDORS
                }
                animateOpacity
              >
                <ControlledSelect
                  name="vendor_ids"
                  label="Vendor IDs"
                  mode="tags"
                  options={[]}
                  layout="stacked"
                  placeholder="Enter vendor IDs"
                  open={false}
                  // eslint-disable-next-line react/no-unstable-nested-components
                  suffixIcon={<span />}
                  tooltip="List the specific vendors that are restricted or allowed from processing data for this purpose."
                  disabled={
                    values.vendor_restriction ===
                    TCFVendorRestriction.RESTRICT_ALL_VENDORS
                  }
                  onBlur={() => {
                    // Add small delay to allow Ant Select to create tag before validation
                    setTimeout(() => {
                      setTouched({
                        vendor_ids: true,
                      });
                      validateField("vendor_ids");
                    }, 100);
                  }}
                  onInputKeyDown={(e) => {
                    // disable space and comma keys to help avoid confusion on the expected behavior
                    // eg. prevent attempting to type "123, 1-100" and enter or "123 1-100" and enter
                    if (
                      e.key === " " ||
                      e.code === "Space" ||
                      e.key === "," ||
                      e.code === "Comma"
                    ) {
                      e.preventDefault();
                      e.stopPropagation();
                    }
                  }}
                  helperText="Enter IDs (e.g. 123) or ranges (e.g. 1-10) and press enter"
                  isRequired
                />
              </Collapse>
              <Flex justify="flex-end" className="gap-3 pt-4">
                <Button
                  onClick={onClose}
                  data-testid="cancel-restriction-button"
                >
                  Cancel
                </Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  data-testid="save-restriction-button"
                >
                  Save
                </Button>
              </Flex>
            </Flex>
          </Form>
        )}
      </Formik>
    </FormModal>
  );
};
