/* eslint-disable no-underscore-dangle */
import { FidesEndpointPaths } from "fides-js";
import { API_URL } from "../support/constants";
import { stubConfig } from "../support/stubs";

describe("Fides-js GPP extension", () => {
  beforeEach(() => {
    cy.intercept("PATCH", `${API_URL}${FidesEndpointPaths.NOTICES_SERVED}`, {
      fixture: "consent/notices_served_tcf.json",
    }).as("patchNoticesServed");
  });

  it("does not load the GPP extension if it is not enabled", () => {
    cy.fixture("consent/experience_tcf.json").then((experience) => {
      stubConfig({
        options: {
          isOverlayEnabled: true,
          tcfEnabled: true,
          gppEnabled: false,
        },
        experience: experience.items[0],
      });
    });
    cy.waitUntilFidesInitialized().then(() => {
      cy.get("@FidesUIShown").should("have.been.calledOnce");
      cy.get("div#fides-banner").should("be.visible");
      cy.window().then((win) => {
        expect(win.__gpp).to.eql(undefined);
      });
    });
  });

  describe("with TCF and GPP enabled", () => {
    beforeEach(() => {
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            gppEnabled: true,
          },
          experience: experience.items[0],
        });
      });
    });

    it("loads the gpp extension if it is enabled", () => {
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("have.been.calledOnce");
        cy.get("div#fides-banner").should("be.visible");
        cy.window().then((win) => {
          win.__gpp("ping", cy.stub().as("gppPing"));
          cy.get("@gppPing")
            .should("have.been.calledOnce")
            .its("lastCall.args")
            .then(([data, success]) => {
              expect(success).to.eql(true);
              expect(data.signalStatus).to.eql("not ready");
            });
        });
      });
    });
  });

  describe("with TCF disabled and GPP enabled", () => {
    beforeEach(() => {
      stubConfig({
        options: {
          isOverlayEnabled: true,
          tcfEnabled: false,
          gppEnabled: true,
        },
      });
    });

    it("loads the gpp extension if it is enabled", () => {
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("have.been.calledOnce");
        cy.get("div#fides-banner").should("be.visible");
        cy.window().then((win) => {
          win.__gpp("ping", cy.stub().as("gppPing"));
          cy.get("@gppPing")
            .should("have.been.calledOnce")
            .its("lastCall.args")
            .then(([data, success]) => {
              expect(success).to.eql(true);
              expect(data.signalStatus).to.eql("not ready");
            });
        });
      });
    });
  });
});
