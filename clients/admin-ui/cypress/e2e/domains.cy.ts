import { stubPlus } from "cypress/support/stubs";

import { DOMAIN_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";

// Mock response for GET /api/v1/config?api_set=true
const API_SET_CONFIG = {
  security: {
    cors_origins: ["https://example.com", "https://app.example.com"],
  },
};

// Mock response for GET /api/v1/config?api_set=false
const CONFIG_SET_CONFIG = {
  security: {
    cors_origins: ["http://localhost"],
    cors_origin_regex: "https://.*\\.example\\.com",
  },
};

describe("Domains page", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
  });

  it("can navigate to the Domains page", () => {
    cy.visit("/");
    cy.getByTestId("Domains-nav-link").click();
    cy.getByTestId("management-domains");
  });

  describe("can view domains", () => {
    describe("when existing domains are configured (both api-set and config-set)", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/config?api_set=true", API_SET_CONFIG).as(
          "getApiSetConfig",
        );
        cy.intercept(
          "GET",
          "/api/v1/config?api_set=false",
          CONFIG_SET_CONFIG,
        ).as("getConfigSetConfig");
        cy.visit(DOMAIN_MANAGEMENT_ROUTE);
      });

      it("can display a loading state while fetching domain configuration", () => {
        cy.getByTestId("api-set-domains-form").within(() => {
          cy.get(".chakra-spinner");
        });
        cy.getByTestId("config-set-domains-form").within(() => {
          cy.get(".chakra-spinner");
        });

        // After fetching, spinners should disappear
        cy.wait("@getApiSetConfig");
        cy.wait("@getConfigSetConfig");
        cy.getByTestId("api-set-domains-form").within(() => {
          cy.get(".chakra-spinner").should("not.exist");
        });
        cy.getByTestId("config-set-domains-form").within(() => {
          cy.get(".chakra-spinner").should("not.exist");
        });
      });

      it("can view existing domain configuration, with both api-set and config-set values", () => {
        cy.wait("@getApiSetConfig");
        cy.wait("@getConfigSetConfig");

        cy.getByTestId("api-set-domains-form").within(() => {
          cy.getByTestId("input-cors_origins[0]").should(
            "have.value",
            "https://example.com",
          );
        });

        cy.getByTestId("config-set-domains-form").within(() => {
          cy.getByTestId("input-config_cors_origins[0]").should(
            "have.value",
            "http://localhost",
          );
        });

        cy.getByTestId("input-config_cors_origin_regex").should(
          "have.value",
          "https://.*\\.example\\.com",
        );
      });
    });

    describe("when no existing domains are configured", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/config?api_set=true", {}).as(
          "getApiSetConfig",
        );
        cy.intercept("GET", "/api/v1/config?api_set=false", {}).as(
          "getConfigSetConfig",
        );
        cy.visit(DOMAIN_MANAGEMENT_ROUTE);
      });

      it("can view empty state", () => {
        cy.wait("@getApiSetConfig");
        cy.wait("@getConfigSetConfig");

        cy.getByTestId("api-set-domains-form").within(() => {
          cy.getByTestId("input-cors_origins[0]").should("not.exist");
        });

        cy.getByTestId("config-set-domains-form").within(() => {
          cy.getByTestId("input-config_cors_origins[0]").should("not.exist");
          cy.getByTestId("input-config_cors_origin_regex").should("not.exist");
          cy.contains("No advanced domain settings configured.");
        });
      });
    });
  });

  describe("can edit domains", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/config?api_set=true", API_SET_CONFIG).as(
        "getApiSetConfig",
      );
      cy.intercept("GET", "/api/v1/config?api_set=false", CONFIG_SET_CONFIG).as(
        "getConfigSetConfig",
      );
      cy.visit(DOMAIN_MANAGEMENT_ROUTE);
      cy.wait("@getApiSetConfig");
      cy.wait("@getConfigSetConfig");
    });

    it("can edit an existing domain", () => {
      const API_SET_CONFIG_UPDATED = {
        security: {
          cors_origins: ["https://www.example.com", "https://app.example.com"],
        },
      };
      cy.intercept("PUT", "/api/v1/config", { statusCode: 200 }).as(
        "putApiSetConfig",
      );
      cy.intercept(
        "GET",
        "/api/v1/config?api_set=true",
        API_SET_CONFIG_UPDATED,
      ).as("getApiSetConfig");

      // Edit the first domain and save our changes
      cy.getByTestId("input-cors_origins[0]")
        .clear()
        .type("https://www.example.com");
      cy.getByTestId("save-btn").click();
      cy.wait("@putApiSetConfig").then((interception) => {
        const { body } = interception.request;
        expect(body)
          .to.have.nested.property("security.cors_origins")
          .to.eql(["https://www.example.com", "https://app.example.com"]);
      });
      cy.wait("@getApiSetConfig");
      cy.getByTestId("input-cors_origins[0]").should(
        "have.value",
        "https://www.example.com",
      );
      cy.getByTestId("toast-success-msg");
    });

    it("can remove an existing domain", () => {
      const API_SET_CONFIG_UPDATED = {
        security: {
          cors_origins: ["https://app.example.com"],
        },
      };
      cy.intercept("PUT", "/api/v1/config", { statusCode: 200 }).as(
        "putApiSetConfig",
      );
      cy.intercept(
        "GET",
        "/api/v1/config?api_set=true",
        API_SET_CONFIG_UPDATED,
      ).as("getApiSetConfig");

      // Delete the first domain and save our changes
      cy.get("[aria-label='delete-domain']:first").click();
      cy.getByTestId("save-btn").click();
      cy.wait("@putApiSetConfig").then((interception) => {
        const { body } = interception.request;
        expect(body)
          .to.have.nested.property("security.cors_origins")
          .to.eql(["https://app.example.com"]);
      });
      cy.wait("@getApiSetConfig");
      cy.getByTestId("input-cors_origins[0]").should(
        "have.value",
        "https://app.example.com",
      );
      cy.getByTestId("toast-success-msg");
    });

    it("can validate domains", () => {
      cy.getByTestId("api-set-domains-form").within(() => {
        cy.getByTestId("input-cors_origins[0]").clear().type("foo").blur();
        cy.root().should("contain", "Domain must be a valid URL");
        cy.getByTestId("save-btn").should("be.disabled");

        cy.getByTestId("input-cors_origins[0]")
          .clear()
          .type("https://*.foo.com")
          .blur();
        cy.root().should("contain", "Domain cannot contain a wildcard");
        cy.getByTestId("save-btn").should("be.disabled");

        cy.getByTestId("input-cors_origins[0]")
          .clear()
          .type("https://foo.com/blog")
          .blur();
        cy.root().should("contain", "Domain cannot contain a path");
        cy.getByTestId("save-btn").should("be.disabled");

        cy.getByTestId("input-cors_origins[0]")
          .clear()
          .type("file://example.txt")
          .blur();
        cy.root().should("contain", "Domain must be a valid URL");
        cy.getByTestId("save-btn").should("be.disabled");

        cy.getByTestId("input-cors_origins[0]")
          .clear()
          .type("http:foo.com")
          .blur();
        cy.root().should("contain", "Domain must be a valid URL");
        cy.getByTestId("save-btn").should("be.disabled");

        cy.getByTestId("input-cors_origins[0]")
          .clear()
          .type("https://foo.com/")
          .blur();
        cy.root().should("contain", "Domain cannot contain a path");
        cy.getByTestId("save-btn").should("be.disabled");

        cy.getByTestId("input-cors_origins[0]")
          .clear()
          .type("https://foo.com")
          .blur();
        cy.getByTestId("save-btn").should("be.enabled");
      });
    });
  });
});
