import FormSection from "~/features/common/form/FormSection";
import { CustomSelect } from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import { DeliveryMechanism } from "~/types/api";

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
 */
const DeliveryMechanismForm = ({ isOverlay }: ExperienceFormRules) => {
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
      />
    </FormSection>
  );
};

export default DeliveryMechanismForm;
