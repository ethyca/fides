import { useFormikContext } from "formik";
import { useEffect, useMemo } from "react";

import FormSection from "~/features/common/form/FormSection";
import { CustomSelect } from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import {
  ComponentType,
  ConsentMechanism,
  DeliveryMechanism,
  PrivacyExperienceCreate,
  PrivacyNoticeResponse,
} from "~/types/api";

const DELIVERY_MECHANISM_OPTIONS = enumToOptions(DeliveryMechanism).map(
  (opt) => ({
    ...opt,
    label: `${opt.label.charAt(0).toUpperCase()}${opt.label.slice(1)}`,
  })
);

/**
 * Delivery mechanism form component
 * Rules:
 *   * Only renders on component_type = OVERLAY
 *   * Must be "Banner" if there are any "opt-in" notices
 */
const DeliveryMechanismForm = ({
  privacyNotices,
}: {
  privacyNotices?: PrivacyNoticeResponse[];
}) => {
  const { initialValues, setFieldValue } =
    useFormikContext<PrivacyExperienceCreate>();

  const needsBanner = useMemo(() => {
    return (
      privacyNotices &&
      privacyNotices.some(
        (notice) =>
          notice.consent_mechanism === ConsentMechanism.OPT_IN ||
          notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY
      )
    );
  }, [privacyNotices]);

  useEffect(() => {
    if (needsBanner) {
      setFieldValue("delivery_mechanism", DeliveryMechanism.BANNER);
    }
  }, [needsBanner, setFieldValue]);

  if (initialValues.component === ComponentType.PRIVACY_CENTER) {
    return null;
  }

  return (
    <FormSection
      title="Delivery mechanism"
      data-testid="delivery-mechanism-form"
    >
      <CustomSelect
        name="delivery_mechanism"
        label="Choose your delivery mechanism"
        options={DELIVERY_MECHANISM_OPTIONS}
        variant="stacked"
        isDisabled={needsBanner}
      />
    </FormSection>
  );
};

export default DeliveryMechanismForm;
