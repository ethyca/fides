import { UpdateConsentValidation } from "../../src/lib/consent-types";
import { getCoreFides } from "../../src/lib/init-utils";

describe("init-utils", () => {
  describe("updateExperience", () => {
    it("should reject when neither consent nor fidesString is provided", async () => {
      const fides = getCoreFides({ tcfEnabled: false });
      expect(() => {
        fides.updateConsent({});
      }).toThrow("Either consent or fidesString must be provided");
    });

    it("should handle different validation modes", async () => {
      const fides = getCoreFides({ tcfEnabled: false });

      // Test invalid validation option
      expect(() => {
        fides.updateConsent({
          consent: { analytics: true },
          validation: "invalid" as UpdateConsentValidation,
        });
      }).toThrow(/Validation must be one of/);
    });
  });
});
