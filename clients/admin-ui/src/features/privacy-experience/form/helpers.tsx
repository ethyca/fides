import {
  ComponentType,
  DeliveryMechanism,
  PrivacyExperienceCreate,
  PrivacyExperienceResponse,
} from "~/types/api";

export const defaultInitialValues: PrivacyExperienceCreate = {
  regions: [],
  component: ComponentType.OVERLAY,
  delivery_mechanism: DeliveryMechanism.LINK,
};

export const transformPrivacyExperienceResponseToCreation = (
  experience: PrivacyExperienceResponse
): PrivacyExperienceCreate => {
  // Remove the fields not needed for editing/creation
  const {
    created_at: createdAt,
    updated_at: updatedAt,
    privacy_experience_history_id: historyId,
    privacy_experience_template_id: templateId,
    version,
    privacy_notices: notices,
    ...rest
  } = experience;
  return {
    ...rest,

    regions: experience.regions ?? defaultInitialValues.regions,
    component: experience.component ?? defaultInitialValues.component,
    delivery_mechanism:
      experience.delivery_mechanism ?? defaultInitialValues.delivery_mechanism,
  };
};
