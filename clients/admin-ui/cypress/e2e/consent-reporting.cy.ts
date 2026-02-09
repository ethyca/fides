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
      cy.getByTestId("consent-reporting-table").should("exist");
    });
    it("can't access without plus", () => {
      stubPlus(false);
      cy.visit(CONSENT_REPORTING_ROUTE);
      cy.getByTestId("home-content");
    });
  });

  describe("results view and download report", () => {
    beforeEach(() => {
      stubPlus(true);
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
    it("can lookup specific consent preferences", () => {
      cy.intercept({
        url: "/api/v1/current-privacy-preferences*",
        method: "GET",
      }).as("lookupConsentPreferences");
      cy.getByTestId("consent-reporting-dropdown-btn").click();
      cy.getByTestId("consent-preference-lookup-btn").click();
      cy.getByTestId("subject-search-input").type("test@example.com{enter}");
      cy.wait("@lookupConsentPreferences").then((interception) => {
        const { url: requestUrl } = interception.request;
        let url = new URL(requestUrl);
        let params = new URLSearchParams(url.search);
        expect(params.get("email")).to.equal("test@example.com");
        expect(params.get("phone_number")).to.equal("test@example.com");
        expect(params.get("fides_user_device_id")).to.equal("test@example.com");
        expect(params.get("external_id")).to.equal("test@example.com");
      });
    });
    it("shows consent preferences table after lookup", () => {
      cy.intercept(
        {
          url: "/api/v1/current-privacy-preferences*",
          method: "GET",
        },
        {
          fixture: "consent-reporting/consent-lookup.json",
        },
      ).as("lookupConsentPreferences");

      cy.getByTestId("consent-reporting-dropdown-btn").click();
      cy.getByTestId("consent-preference-lookup-btn").click();
      cy.getByTestId("subject-search-input").type("test@example.com{enter}");

      cy.wait("@lookupConsentPreferences");
      cy.get("#chakra-modal-consent-lookup-modal").within(() => {
        cy.getByTestId("fidesTable-body").should("exist");
        cy.getByTestId("fidesTable-body").find("tr").should("have.length", 5);
      });
    });
    it("shows TCF details table and filters out system and vendor records", () => {
      cy.intercept(
        {
          url: "/api/v1/current-privacy-preferences*",
          method: "GET",
        },
        {
          fixture: "consent-reporting/tcf-consent-lookup.json",
        },
      ).as("lookupConsentPreferences");

      cy.getByTestId("consent-reporting-dropdown-btn").click();
      cy.getByTestId("consent-preference-lookup-btn").click();
      cy.getByTestId("subject-search-input").type("test@example.com{enter}");

      cy.wait("@lookupConsentPreferences");
      cy.getByTestId("fidesTable").should("exist");

      cy.getByTestId("fidesTable")
        .find("tr")
        .each(($row) => {
          const text = $row.text();
          expect(text).to.not.include("vendor_");
          expect(text).to.not.include("system_");
        });
    });
    it("loads the consent report table without date filters", () => {
      cy.intercept(
        {
          url: "/api/v1/historical-privacy-preferences*",
          method: "GET",
        },
        {
          fixture: "consent-reporting/historical-privacy-preferences.json",
        },
      ).as("getConsentReport");

      cy.wait("@getConsentReport").then((interception) => {
        const { url: requestUrl } = interception.request;
        let url = new URL(requestUrl);
        let params = new URLSearchParams(url.search);
        expect(params.get("request_timestamp_gt")).to.be.null;
        expect(params.get("request_timestamp_lt")).to.be.null;
      });

      cy.getByTestId("consent-reporting-table")
        .find("tr")
        .should("have.length", 24);
    });
    it("loads the consent report table with date filters", () => {
      cy.intercept(
        {
          url: "/api/v1/historical-privacy-preferences*",
          method: "GET",
        },
        {
          fixture: "consent-reporting/historical-privacy-preferences.json",
        },
      ).as("getConsentReport");

      cy.wait("@getConsentReport");

      cy.getByTestId("input-date-range").first().type("2023-11-01");
      cy.getByTestId("input-date-range").last().type("2023-11-07{enter}");

      cy.wait("@getConsentReport").then((interception) => {
        const { url: requestUrl } = interception.request;
        let url = new URL(requestUrl);
        let params = new URLSearchParams(url.search);

        // Calculate expected timestamps accounting for local timezone
        const startDate = new Date("2023-11-01T00:00:00");
        const endDate = new Date("2023-11-07T23:59:59.999");
        const expectedStartTimestamp = startDate.toISOString();
        const expectedEndTimestamp = endDate.toISOString();

        expect(params.get("request_timestamp_gt")).to.equal(
          expectedStartTimestamp,
        );
        expect(params.get("request_timestamp_lt")).to.equal(
          expectedEndTimestamp,
        );
      });

      cy.getByTestId("consent-reporting-table")
        .find("tr")
        .should("have.length", 24);
    });
  });

  describe("TCF consent", () => {
    beforeEach(() => {
      stubPlus(true);
      cy.visit(CONSENT_REPORTING_ROUTE);
      cy.intercept(
        {
          url: "/api/v1/historical-privacy-preferences*",
          method: "GET",
        },
        {
          fixture: "consent-reporting/historical-privacy-preferences.json",
        },
      ).as("getConsentReport");
      cy.wait("@getConsentReport");
    });

    it("displays TCF badge and is clickable", () => {
      cy.getByTestId("consent-reporting-table")
        .find("tr")
        .eq(3)
        .findByTestId("tcf-badge")
        .within(() => {
          cy.get("button").should("exist");
        });
    });

    it("shows TCF details table and excludes system and vendor records", () => {
      cy.getByTestId("consent-reporting-table")
        .find("tr")
        .eq(3)
        .findByTestId("tcf-badge")
        .within(() => {
          cy.get("button").click();
        });

      cy.getByTestId("consent-tcf-detail-modal").should("exist");
      cy.getByTestId("fidesTable").should("exist");

      cy.getByTestId("fidesTable")
        .find("tr")
        .each(($row) => {
          const text = $row.text();
          expect(text).to.not.include("vendor_");
          expect(text).to.not.include("system_");
        });
    });
  });
});
