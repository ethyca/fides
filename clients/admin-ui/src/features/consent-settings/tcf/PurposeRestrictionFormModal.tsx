import {
  Button,
  Flex,
  Form,
  Select,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import isEqual from "lodash/isEqual";
import { useEffect, useMemo, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import ConfirmCloseModal from "~/features/common/modals/ConfirmCloseModal";
import {
  TCFPublisherRestrictionRequest,
  TCFRestrictionType,
  TCFVendorRestriction,
} from "~/types/api";

import {
  FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS,
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
  const message = useMessage();
  const [createRestriction] = useCreatePublisherRestrictionMutation();
  const [updateRestriction] = useUpdatePublisherRestrictionMutation();
  const isPurposeFlexible = !(
    purposeId && FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS.includes(+purposeId)
  );

  const usedRestrictionTypes = existingRestrictions
    .filter((r) => r.id !== restrictionId)
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
      disabled: usedRestrictionTypes.length > 0,
      title:
        usedRestrictionTypes.length > 0
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

  const computedInitialValues = useMemo(
    () => ({
      ...initialValues,
      restriction_type: isPurposeFlexible
        ? initialValues.restriction_type
        : TCFRestrictionType.PURPOSE_RESTRICTION,
    }),
    [initialValues, isPurposeFlexible],
  );

  const [form] = Form.useForm<FormValues>();

  const allValues = Form.useWatch([], form);
  const vendorRestriction = Form.useWatch("vendor_restriction", form);
  const restrictionType = Form.useWatch("restriction_type", form);
  const [submittable, setSubmittable] = useState(false);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, allValues]);

  const isDirty = useMemo(
    () => !isEqual(allValues, computedInitialValues),
    [allValues, computedInitialValues],
  );

  const showVendorIds =
    !!restrictionType &&
    !!vendorRestriction &&
    vendorRestriction !== TCFVendorRestriction.RESTRICT_ALL_VENDORS;

  // Clear vendor_ids when switching to "restrict all vendors" since the field
  // unmounts and stale values would otherwise persist in the form store.
  useEffect(() => {
    if (vendorRestriction === TCFVendorRestriction.RESTRICT_ALL_VENDORS) {
      form.setFieldValue("vendor_ids", []);
    }
  }, [vendorRestriction, form]);

  const handleSubmit = async (values: FormValues): Promise<void> => {
    try {
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
          message.error("Failed to update restriction");
          return;
        }
        message.success("Restriction updated successfully");
      } else {
        const result = await createRestriction({
          configuration_id: configurationId,
          restriction: requestWithPurposeId,
        });
        if (isErrorResult(result)) {
          message.error("Failed to create restriction");
          return;
        }
        message.success("Restriction created successfully");
      }
      onClose();
    } catch (error) {
      message.error("Failed to save restriction");
    }
  };

  const handleClose = () => {
    form.resetFields();
    onClose();
  };

  return (
    <ConfirmCloseModal
      open={isOpen}
      onClose={handleClose}
      getIsDirty={() => isDirty}
      centered
      destroyOnHidden
      title="Edit restriction"
      footer={null}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={computedInitialValues}
        key={restrictionId ?? "create"}
      >
        <Flex vertical>
          <Typography.Text>
            Define how specific vendors are restricted from processing data for
            this purpose. Select a restriction type, set whether the listed
            vendors are restricted or allowed, and specify which vendor IDs the
            restriction applies to.
          </Typography.Text>
          <Form.Item
            name="restriction_type"
            label="Restriction type"
            tooltip="Choose how vendors are permitted to process data for this purpose. This setting overrides the vendor's declared legal basis in the Global Vendor List."
            rules={[
              { required: true, message: "Restriction type is required" },
            ]}
          >
            <Tooltip
              title={
                !isPurposeFlexible
                  ? "Non-flexible purposes only support Purpose restrictions and cannot be restricted by consent or legitimate interest settings."
                  : undefined
              }
            >
              <Select
                aria-label="Restriction type"
                options={restrictionTypeOptions}
                disabled={!isPurposeFlexible}
                data-testid="controlled-select-restriction_type"
                className="w-full"
              />
            </Tooltip>
          </Form.Item>
          <Form.Item
            name="vendor_restriction"
            label="Vendor restriction"
            tooltip="Decide if the restriction applies to all vendors, specific vendors, or if only certain vendors are allowed."
            rules={[
              { required: true, message: "Vendor restriction is required" },
            ]}
          >
            <Select
              aria-label="Vendor restriction"
              options={vendorRestrictionOptions}
              data-testid="controlled-select-vendor_restriction"
            />
          </Form.Item>
          {showVendorIds && (
            <Form.Item
              name="vendor_ids"
              label="Vendor IDs"
              tooltip="List the specific vendors that are restricted or allowed from processing data for this purpose."
              extra="Enter IDs (e.g. 123) or ranges (e.g. 1-10) and press enter"
              dependencies={["vendor_restriction"]}
              rules={[
                {
                  required: true,
                  message: "At least one vendor ID is required",
                },
                {
                  validator: (_, value) => {
                    if (
                      value?.length &&
                      !value.every((id: string) => isValidVendorIdFormat(id))
                    ) {
                      return Promise.reject(
                        new Error(
                          "Vendor IDs must be numbers or ranges (e.g., 10 or 15-300)",
                        ),
                      );
                    }
                    return Promise.resolve();
                  },
                },
                {
                  validator: (_, value) => {
                    const currentValues = form.getFieldsValue(true);
                    if (
                      checkForVendorRestrictionConflicts(
                        { ...currentValues, vendor_ids: value } as FormValues,
                        existingRestrictions,
                        purposeId,
                        restrictionId,
                      )
                    ) {
                      return Promise.reject(new Error(ERROR_MESSAGE));
                    }
                    return Promise.resolve();
                  },
                },
              ]}
            >
              <Select
                aria-label="Vendor IDs"
                mode="tags"
                options={[]}
                placeholder="Enter vendor IDs"
                open={false}
                suffixIcon={<span />}
                tokenSeparators={[",", " "]}
                data-testid="controlled-select-vendor_ids"
              />
            </Form.Item>
          )}
          <Flex justify="flex-end" className="gap-3 pt-4">
            <Button onClick={handleClose} data-testid="cancel-restriction-button">
              Cancel
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              disabled={!submittable || !isDirty}
              data-testid="save-restriction-button"
            >
              Save
            </Button>
          </Flex>
        </Flex>
      </Form>
    </ConfirmCloseModal>
  );
};
