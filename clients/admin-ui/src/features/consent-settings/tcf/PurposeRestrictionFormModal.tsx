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
import FormModal from "~/features/common/modals/FormModal";
import { successToastParams } from "~/features/common/toast";
import { TCFRestrictionType, TCFVendorRestriction } from "~/types/api";

import {
  RESTRICTION_TYPE_LABELS,
  VENDOR_RESTRICTION_LABELS,
} from "./constants";
import { FormValues, PurposeRestriction } from "./types";
import {
  checkForVendorRestrictionConflicts,
  ERROR_MESSAGE,
  isValidVendorIdFormat,
} from "./validation-utils";

interface PurposeRestrictionFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialValues?: FormValues;
  existingRestrictions?: PurposeRestriction[];
  purposeId?: number;
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
}: PurposeRestrictionFormModalProps) => {
  const toast = useToast();

  const restrictionTypeOptions = [
    {
      value: TCFRestrictionType.PURPOSE_RESTRICTION,
      label: RESTRICTION_TYPE_LABELS[TCFRestrictionType.PURPOSE_RESTRICTION],
    },
    {
      value: TCFRestrictionType.REQUIRE_CONSENT,
      label: RESTRICTION_TYPE_LABELS[TCFRestrictionType.REQUIRE_CONSENT],
    },
    {
      value: TCFRestrictionType.REQUIRE_LEGITIMATE_INTEREST,
      label:
        RESTRICTION_TYPE_LABELS[TCFRestrictionType.REQUIRE_LEGITIMATE_INTEREST],
    },
  ];

  const vendorRestrictionOptions = [
    {
      value: TCFVendorRestriction.RESTRICT_ALL_VENDORS,
      label:
        VENDOR_RESTRICTION_LABELS[TCFVendorRestriction.RESTRICT_ALL_VENDORS],
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
              ),
          ),
      otherwise: (schema) =>
        schema.test(
          "no-conflicts-restrict-all",
          ERROR_MESSAGE,
          (_, context) =>
            !checkForVendorRestrictionConflicts(
              context.parent as FormValues,
              existingRestrictions,
              purposeId,
            ),
        ),
    }),
  });

  const handleSubmit = (values: FormValues) => {
    // TASK: Submit to API
    console.log("Form values:", values);
    toast(successToastParams("Restriction updated successfully"));
    onClose();
  };

  return (
    <FormModal isOpen={isOpen} onClose={onClose} title="Edit restriction">
      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
        validationSchema={validationSchema}
      >
        {({ values }) => (
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
                  placeholder="Enter a single ID or range of IDs and press enter"
                  open={false}
                  // eslint-disable-next-line react/no-unstable-nested-components
                  suffixIcon={<span />}
                  tooltip="List the specific vendors that are restricted or allowed from processing data for this purpose. Enter a single vendor ID or a range of IDs and press enter."
                  disabled={
                    values.vendor_restriction ===
                    TCFVendorRestriction.RESTRICT_ALL_VENDORS
                  }
                />
              </Collapse>

              <Flex justify="flex-end" className="gap-3 pt-4">
                <Button onClick={onClose}>Cancel</Button>
                <Button type="primary" htmlType="submit">
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
