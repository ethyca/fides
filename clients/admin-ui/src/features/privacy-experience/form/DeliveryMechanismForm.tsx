import { useFormikContext } from "formik";
import { useEffect } from "react";

import FormSection from "~/features/common/form/FormSection";
import { CustomSelect } from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import { DeliveryMechanism, PrivacyExperienceCreate } from "~/types/api";

import { ExperienceFormRules } from "./helpers";

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
  needsBanner,
  isOverlay,
}: ExperienceFormRules) => {
  const { setFieldValue } = useFormikContext<PrivacyExperienceCreate>();

  useEffect(() => {
    if (needsBanner) {
      setFieldValue("delivery_mechanism", DeliveryMechanism.BANNER);
    }
  }, [needsBanner, setFieldValue]);

  if (!isOverlay) {
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
