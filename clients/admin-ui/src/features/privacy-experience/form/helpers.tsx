import * as Yup from "yup";

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
    version,
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

export const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Title"),
  data_uses: Yup.array(Yup.string())
    .min(1, "Must assign at least one data use")
    .label("Data uses"),
  regions: Yup.array(Yup.string())
    .min(1, "Must assign at least one location")
    .label("Locations"),
});
