import { stubConfig } from "../support/stubs";

describe("Consent i18n", () => {
  beforeEach(() => {
    stubConfig({});
  });

  it("should render the banner", () => {
    cy.get("div#fides-banner-description.fides-banner-description").contains(
      "[banner-opts] We use cookies and similar methods"
    );
  });
});
