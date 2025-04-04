import {
  AntButton as Button,
  AntFlex as Flex,
  Collapse,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import FormModal from "~/features/common/modals/FormModal";
import { successToastParams } from "~/features/common/toast";

import {
  RESTRICTION_TYPE_LABELS,
  RestrictionType,
  VENDOR_RESTRICTION_LABELS,
  VendorRestriction,
} from "./constants";

interface PurposeRestrictionFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialValues?: FormValues;
}

interface FormValues {
  restriction_type: string;
  vendor_restriction: string;
  vendor_ids?: string[];
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
}: PurposeRestrictionFormModalProps) => {
  const toast = useToast();

  const restrictionTypeOptions = [
    {
      value: RestrictionType.PURPOSE_RESTRICTION,
      label: RESTRICTION_TYPE_LABELS[RestrictionType.PURPOSE_RESTRICTION],
    },
    {
      value: RestrictionType.REQUIRE_CONSENT,
      label: RESTRICTION_TYPE_LABELS[RestrictionType.REQUIRE_CONSENT],
    },
    {
      value: RestrictionType.REQUIRE_LEGITIMATE_INTEREST,
      label:
        RESTRICTION_TYPE_LABELS[RestrictionType.REQUIRE_LEGITIMATE_INTEREST],
    },
  ];

  const vendorRestrictionOptions = [
    {
      value: VendorRestriction.RESTRICT_ALL,
      label: VENDOR_RESTRICTION_LABELS[VendorRestriction.RESTRICT_ALL],
    },
    {
      value: VendorRestriction.RESTRICT_SPECIFIC,
      label: VENDOR_RESTRICTION_LABELS[VendorRestriction.RESTRICT_SPECIFIC],
    },
    {
      value: VendorRestriction.ALLOW_SPECIFIC,
      label: VENDOR_RESTRICTION_LABELS[VendorRestriction.ALLOW_SPECIFIC],
    },
  ];

  const handleSubmit = (values: FormValues) => {
    // TASK: Submit to API
    console.log("Form values:", values);
    toast(successToastParams("Restriction updated successfully"));
    onClose();
  };

  return (
    <FormModal isOpen={isOpen} onClose={onClose} title="Edit restriction">
      <Formik initialValues={initialValues} onSubmit={handleSubmit}>
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
                  values.vendor_restriction !== VendorRestriction.RESTRICT_ALL
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
                    values.vendor_restriction === VendorRestriction.RESTRICT_ALL
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
