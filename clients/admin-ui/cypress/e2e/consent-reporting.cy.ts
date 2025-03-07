import { stubPlus } from "cypress/support/stubs";

import { CONSENT_REPORTING_ROUTE } from "~/features/common/nav/routes";

describe("Consent reporting", () => {
  beforeEach(() => {
    cy.login();
  });

  describe("access", () => {
    it("can access the consent reporting page", () => {
      stubPlus(true, {
        core_fides_version: "1.9.6",
        fidesplus_server: "healthy",
        fidesplus_version: "1.9.6",
        system_scanner: {
          enabled: false,
          cluster_health: null,
          cluster_error: null,
        },
        dictionary: {
          enabled: false,
          service_health: null,
          service_error: null,
        },
        tcf: {
          enabled: false,
        },
        fides_cloud: {
          enabled: false,
        },
      });
      cy.visit(CONSENT_REPORTING_ROUTE);
      cy.getByTestId("consent-reporting");
    });
    it("can't access without plus", () => {
      stubPlus(false);
      cy.visit(CONSENT_REPORTING_ROUTE);
      cy.getByTestId("home-content");
    });
  });

  describe("downloading reports", () => {
    beforeEach(() => {
      stubPlus(true, {
        core_fides_version: "1.9.6",
        fidesplus_server: "healthy",
        fidesplus_version: "1.9.6",
        system_scanner: {
          enabled: false,
          cluster_health: null,
          cluster_error: null,
        },
        dictionary: {
          enabled: false,
          service_health: null,
          service_error: null,
        },
        tcf: {
          enabled: false,
        },
        fides_cloud: {
          enabled: false,
        },
      });
      cy.visit(CONSENT_REPORTING_ROUTE);
    });
    it("can request a report", () => {
      cy.intercept({
        url: "/api/v1/plus/consent_reporting*",
        method: "GET",
      }).as("getConsentReport");
      cy.getByTestId("input-date-range").first().type("2023-11-01");
      cy.getByTestId("input-date-range").last().type("2023-11-07");
      cy.getByTestId("download-btn").click();
      cy.getByTestId("download-report-btn").click();
      cy.wait("@getConsentReport");
    });
  });
});
