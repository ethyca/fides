import { UserGeolocation } from "fides-js";
import { NextApiRequest } from "next";

import { PrivacyCenterEnvironment } from "~/app/server-environment";

/**
 * Verifies that certain conditions are met to be able to fetch experiences by property ID
 */
export const safeLookupPropertyId = (
  req: NextApiRequest,
  geolocation: UserGeolocation | null,
  environment: PrivacyCenterEnvironment,
  fidesString: string | null,
) => {
  const propertyId = req.query.property_id;

  if (typeof propertyId === "string") {
    if (!geolocation) {
      throw new Error(
        "Geolocation must be provided if a property_id is specified.",
      );
    }
    if (!environment.settings.IS_OVERLAY_ENABLED) {
      throw new Error(
        "IS_OVERLAY_ENABLED must be enabled in environment settings if a property_id is specified.",
      );
    }
    if (!environment.settings.IS_PREFETCH_ENABLED) {
      throw new Error(
        "IS_PREFETCH_ENABLED must be enabled in environment settings if a property_id is specified.",
      );
    }
    if (fidesString) {
      throw new Error(
        "FIDES_STRING must not be provided if a property_id is specified.",
      );
    }
  } else if (Array.isArray(propertyId)) {
    throw new Error("Invalid property_id: only one value must be provided.");
  }

  return propertyId;
};
