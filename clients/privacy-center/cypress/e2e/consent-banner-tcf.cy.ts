import { CONSENT_COOKIE_NAME } from "fides-js";
import { stubConfig } from "../support/stubs";

describe("Fides-js TCF", () => {
  beforeEach(() => {
    cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
    cy.fixture("consent/experience_tcf.json").then((experience) => {
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
        experience: experience.items[0],
      });
    });
  });
  it("can render the TCF modal", () => {});
});
