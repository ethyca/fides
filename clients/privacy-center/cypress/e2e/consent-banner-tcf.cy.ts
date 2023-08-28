import { CONSENT_COOKIE_NAME } from "fides-js";
import { stubConfig } from "../support/stubs";

const PURPOSE_1 = {
  id: 4,
  name: "Use profiles to select personalised advertising",
};
const PURPOSE_2 = {
  id: 9,
  name: "Understand audiences through statistics or combinations of data from different sources",
};
const PURPOSE_3 = {
  id: 6,
  name: "Use profiles to select personalised content",
};
const PURPOSE_4 = {
  id: 7,
  name: "Use profiles to select personalised content",
};
const PURPOSE_5 = {
  id: 2,
  name: "Use profiles to select personalised content",
};
const SPECIAL_PURPOSE_1 = {
  id: 1,
  name: "Ensure security, prevent and detect fraud, and fix errors",
};
const VENDOR_1 = {
  id: "Fides System",
  name: "Fides System",
};
const VENDOR_2 = {
  id: "2",
  name: "amplitude",
};
const STACK_1 = {
  id: 7,
  name: "Personalised ads display, ad measurement, and audience insights",
};
const STACK_2 = {
  id: 28,
  name: "Personalised ads and content display",
};

describe("Fides-js TCF", () => {
  beforeEach(() => {
    cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
    cy.fixture("consent/experience_tcf.json").then((experience) => {
      stubConfig({
        options: {
          isOverlayEnabled: true,
          tcfEnabled: true,
        },
        experience: experience.items[0],
      });
    });
  });

  describe("initial layer", () => {
    beforeEach(() => {
      cy.get("#fides-modal-link").click();
    });

    it("can render purposes in the initial layer as a stack", () => {
      cy.get("span").contains(STACK_1.name);
      cy.get("span").contains(STACK_2.name);

      cy.get("span").contains(STACK_1.name).click();
      [PURPOSE_1.id, PURPOSE_2.id, PURPOSE_4.id, PURPOSE_5.id].forEach((id) => {
        cy.get("li").contains(`Purpose ${id}`);
      });

      cy.get("span").contains(STACK_1.name).click();
      [PURPOSE_5.id, PURPOSE_1.id, PURPOSE_3.id].forEach((id) => {
        cy.get("li").contains(`Purpose ${id}`);
      });
    });
  });

  describe("second layer", () => {
    beforeEach(() => {
      cy.get("#fides-modal-link").click();
      cy.getByTestId("fides-modal-content").within(() => {
        cy.get("#fides-banner-button-secondary")
          .contains("Manage preferences")
          .click();
      });
    });

    describe("rendering the TCF modal", () => {
      it("can render tabs", () => {
        cy.get("#fides-tab-Purposes");
        // Purposes
        cy.getByTestId("toggle-Purposes").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId(`toggle-${PURPOSE_1.name}`).within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Special purposes").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId(`toggle-${SPECIAL_PURPOSE_1.name}`).within(() => {
          cy.get("input").should("be.checked");
        });
        // TODO: add tests once we have features
        cy.get("#fides-tab-Features");

        // Vendors
        cy.get("#fides-tab-Vendors").click();
        cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
          cy.get("input").should("be.checked");
        });
      });

      it("can render GVL badge on vendors and filter", () => {
        cy.get("#fides-tab-Vendors").click();
        cy.get("span")
          .contains(VENDOR_1.name)
          .within(() => {
            cy.get("span").should("not.exist");
          });
        cy.get("span")
          .contains(VENDOR_2.name)
          .within(() => {
            cy.get("span").contains("GVL");
          });

        // Filter to just GVL
        cy.get(".fides-filter-button-group").within(() => {
          cy.get("button").contains("GVL vendors").click();
        });
        cy.get("span").contains(VENDOR_1.name).should("not.exist");
        cy.get("span").contains(VENDOR_2.name);
      });

      it("can group toggle", () => {
        // Toggle the parent toggle off
        cy.getByTestId("toggle-Purposes").click();
        cy.getByTestId(`toggle-${PURPOSE_1.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
        // Toggle a child back on
        cy.getByTestId(`toggle-${PURPOSE_1.name}`).click();
        cy.getByTestId("toggle-Purposes").within(() => {
          cy.get("input").should("not.be.checked");
        });
      });
    });

    describe("saving preferences", () => {
      it("can opt in to all", () => {
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.purpose_preferences).to.eql([
              { id: PURPOSE_5.id, preference: "opt_in" },
              { id: PURPOSE_1.id, preference: "opt_in" },
              { id: PURPOSE_3.id, preference: "opt_in" },
              { id: PURPOSE_4.id, preference: "opt_in" },
              { id: PURPOSE_2.id, preference: "opt_in" },
            ]);
            expect(body.special_purpose_preferences).to.eql([
              { id: SPECIAL_PURPOSE_1.id, preference: "opt_in" },
            ]);
            expect(body.vendor_preferences).to.eql([
              { id: VENDOR_2.id, preference: "opt_in" },
            ]);
            expect(body.system_preferences).to.eql([
              { id: VENDOR_1.id, preference: "opt_in" },
            ]);
          });
        });
      });
      it("can opt out of all", () => {
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt out of all").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.purpose_preferences).to.eql([
              { id: PURPOSE_5.id, preference: "opt_out" },
              { id: PURPOSE_1.id, preference: "opt_out" },
              { id: PURPOSE_3.id, preference: "opt_out" },
              { id: PURPOSE_4.id, preference: "opt_out" },
              { id: PURPOSE_2.id, preference: "opt_out" },
            ]);
            expect(body.special_purpose_preferences).to.eql([
              { id: SPECIAL_PURPOSE_1.id, preference: "opt_out" },
            ]);
            expect(body.vendor_preferences).to.eql([
              { id: VENDOR_2.id, preference: "opt_out" },
            ]);
            expect(body.system_preferences).to.eql([
              { id: VENDOR_1.id, preference: "opt_out" },
            ]);
          });
        });
      });

      it("can opt in to some and opt out of others", () => {
        cy.getByTestId("consent-modal").within(() => {
          cy.getByTestId(`toggle-${PURPOSE_1.name}`).click();
          cy.getByTestId(`toggle-${SPECIAL_PURPOSE_1.name}`).click();
          cy.get("#fides-tab-Vendors").click();
          cy.getByTestId(`toggle-${VENDOR_1.name}`).click();
          cy.get("button").contains("Save").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.purpose_preferences).to.eql([
              { id: PURPOSE_5.id, preference: "opt_in" },
              { id: PURPOSE_1.id, preference: "opt_out" },
              { id: PURPOSE_3.id, preference: "opt_in" },
              { id: PURPOSE_4.id, preference: "opt_in" },
              { id: PURPOSE_2.id, preference: "opt_in" },
            ]);
            expect(body.special_purpose_preferences).to.eql([
              { id: SPECIAL_PURPOSE_1.id, preference: "opt_out" },
            ]);
            expect(body.vendor_preferences).to.eql([
              { id: VENDOR_2.id, preference: "opt_in" },
            ]);
            expect(body.system_preferences).to.eql([
              { id: VENDOR_1.id, preference: "opt_out" },
            ]);
          });
        });
      });
    });
  });
});
