import {
  stubLanguages,
  stubPlus,
  stubPrivacyNoticesCrud,
  stubTaxonomyEntities,
  stubTranslationConfig,
} from "cypress/support/stubs";

import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

const ESSENTIAL_NOTICE_ID = "pri_a518b4d0-9cbc-48b1-94dc-2fe911537b8e";

describe("Privacy notices", () => {
  beforeEach(() => {
    cy.login();
    stubPrivacyNoticesCrud();
    stubTranslationConfig(true);
    stubPlus(true);
    stubLanguages();
  });

  describe("permissions", () => {
    it("should not be viewable for approvers", () => {
      cy.assumeRole(RoleRegistryEnum.APPROVER);
      cy.visit(PRIVACY_NOTICES_ROUTE);
      // should be redirected to the home page
      cy.getByTestId("home-content");
    });

    it("should be visible to everyone else", () => {
      [
        RoleRegistryEnum.CONTRIBUTOR,
        RoleRegistryEnum.OWNER,
        RoleRegistryEnum.VIEWER,
      ].forEach((role) => {
        cy.assumeRole(role);
        cy.visit(PRIVACY_NOTICES_ROUTE);
        cy.getByTestId("privacy-notices-page");
      });
    });

    it("viewers and approvers cannot click into a notice to edit", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_NOTICES_ROUTE);
          cy.wait("@getNotices");
          cy.get("table").contains("tr", "Essential").click();
          cy.getByTestId("privacy-notice-detail-page").should("not.exist");
          cy.getByTestId("privacy-notices-page");
        },
      );
    });

    it("viewers and approvers cannot toggle the enable toggle", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_NOTICES_ROUTE);
          cy.wait("@getNotices");
          cy.get(".toggle").should("not.exist");
        },
      );
    });

    it("viewers and approvers cannot add notices", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_NOTICES_ROUTE);
          cy.wait("@getNotices");
          cy.getByTestId("privacy-notices-page");
          cy.getByTestId("add-privacy-notice-btn").should("not.exist");
        },
      );
    });
  });

  describe("table", () => {
    beforeEach(() => {
      cy.visit(PRIVACY_NOTICES_ROUTE);
      cy.wait("@getNotices");
      stubTaxonomyEntities();
    });

    it("should render a row for each privacy notice", () => {
      [
        "Essential",
        "Functional",
        "Analytics",
        "Marketing",
        "Data Sales and Sharing",
      ].forEach((name) => {
        cy.get("table").contains("tr", name);
      });
    });

    it.skip("can sort", () => {
      cy.get("tbody > tr").first().should("contain", "Data Sales");
      // sort alphabetical
      cy.getByTestId("column-Title").click();
      cy.get("tbody > tr").first().should("contain", "Advertising");

      // sort reverse
      cy.getByTestId("column-Title").click();
      cy.get("tbody > tr").first().should("contain", "Functional");
    });

    it("can click a row to go to the notice page", () => {
      cy.intercept("GET", "/api/v1/privacy-notice/pri*", {
        fixture: "privacy-notices/notice.json",
      }).as("getNoticeDetail");
      cy.get("table").contains("tr", "Essential").click();
      cy.wait("@getNoticeDetail");
      cy.getByTestId("privacy-notice-detail-page");
      cy.url().should("contain", ESSENTIAL_NOTICE_ID);
    });

    it("can click add button to get to a new form", () => {
      cy.getByTestId("add-privacy-notice-btn").click();
      cy.url().should("contain", `${PRIVACY_NOTICES_ROUTE}/new`);
    });

    describe("enabling and disabling", () => {
      beforeEach(() => {});

      it("can enable a notice", () => {
        cy.intercept(
          "PATCH",
          "/api/v1/privacy-notice/*/limited_update*",
          {},
        ).as("toggleEnabled");
        cy.get("table")
          .contains("tr", "Data Sales")
          .within(() => {
            cy.getByTestId("toggle-switch").within(() => {
              cy.get("span").should("not.have.attr", "data-checked");
            });
            cy.getByTestId("toggle-switch").click();
          });

        cy.wait("@toggleEnabled").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql({ disabled: false });
        });
        // redux should requery after invalidation
        cy.wait("@getNotices");
      });

      it("can disable a notice with a warning", () => {
        cy.intercept(
          "PATCH",
          "/api/v1/privacy-notice/*/limited_update*",
          {},
        ).as("toggleEnabled");
        cy.get("table")
          .contains("tr", "Essential")
          .within(() => {
            cy.getByTestId("toggle-switch").should(
              "have.attr",
              "aria-checked",
              "true",
            );
            cy.getByTestId("toggle-switch").click();
          });

        cy.getByTestId("confirmation-modal");
        cy.getByTestId("continue-btn").click();
        cy.wait("@toggleEnabled").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql({ disabled: true });
        });
        // redux should requery after invalidation
        cy.wait("@getNotices");
      });

      it("can render a tag based on systems_applicable", () => {
        // Enabled and has applicable systems
        cy.get("table")
          .contains("tr", "Essential")
          .within(() => {
            cy.getByTestId("status-badge").contains("enabled");
          });
        // Disabled but has applicable systems
        cy.get("table")
          .contains("tr", "Data Sales")
          .within(() => {
            cy.getByTestId("status-badge").contains("available");
          });
        // Disabled and has no applicable systems
        cy.get("table")
          .contains("tr", "Marketing")
          .within(() => {
            cy.getByTestId("status-badge").contains("inactive");
          });
        // Enabled but has no applicable systems.
        // Note: this state should not be possible via only the frontend,
        // but could happen if directly hitting the API
        cy.get("table")
          .contains("tr", "Analytics")
          .within(() => {
            cy.getByTestId("status-badge").contains("inactive");
          });
      });

      it("can show an error if disable toggle fails", () => {
        cy.intercept("PATCH", "/api/v1/privacy-notice/*/limited_update*", {
          statusCode: 422,
          body: {
            detail:
              "Privacy Notice 'Analytics test' has already assigned notice key 'analytics' to region 'PrivacyNoticeRegion.ie'",
          },
        }).as("patchNoticesError");
        cy.get("table")
          .contains("tr", "Data Sales")
          .within(() => {
            cy.get('[data-testid="toggle-switch"]').click();
          });
        cy.wait("@patchNoticesError").then(() => {
          cy.getByTestId("toast-error-msg");
        });
      });
    });
  });

  describe("edit privacy notice", () => {
    beforeEach(() => {
      stubPrivacyNoticesCrud();
      stubTaxonomyEntities();
    });

    it("should render an existing privacy notice", () => {
      cy.visit(`${PRIVACY_NOTICES_ROUTE}/${ESSENTIAL_NOTICE_ID}`);
      cy.wait("@getNoticeDetail");
      cy.fixture("privacy-notices/notice.json").then((notice) => {
        // details section
        cy.getByTestId("input-name").should("have.value", notice.name);

        // consent mechanism section
        cy.getSelectValueContainer("input-consent_mechanism").contains(
          "Notice only",
        );

        cy.getByTestId("notice-locations").within(() => {
          cy.get(".notice-locations--is-disabled");
          cy.get(".notice-locations__value-container").should(
            "contain",
            "United States",
          );
        });

        cy.getByTestId("input-has_gpc_flag").within(() => {
          cy.get("span").should("not.have.attr", "data-checked");
        });

        // configuration section
        notice.data_uses.forEach((dataUse) => {
          cy.getSelectValueContainer("input-data_uses").contains(dataUse);
        });

        // enforcement level
        cy.getSelectValueContainer("input-enforcement_level").contains(
          "Not applicable",
        );

        // translations
        cy.getByTestId("input-translations.0.title").should(
          "have.value",
          notice.translations[0].title,
        );
        cy.getByTestId("input-translations.0.description").should(
          "have.value",
          notice.translations[0].description,
        );
      });
    });

    it("can make an edit", () => {
      cy.intercept("PATCH", "/api/v1/privacy-notice/*", {}).as("patchNotices");
      cy.fixture("privacy-notices/notice.json").then((notice) => {
        cy.visit(`${PRIVACY_NOTICES_ROUTE}/${ESSENTIAL_NOTICE_ID}`);
        cy.wait("@getNoticeDetail");
        const newName = "new name";
        cy.getByTestId("input-name").clear().type(newName);
        // should not reflect the new name since this is the edit form
        cy.getByTestId("input-notice_key").should("have.value", "essential");
        // but we can still update it
        const newKey = "custom_key";
        cy.getByTestId("input-notice_key").clear().type(newKey);

        cy.getByTestId("save-btn").click();
        cy.wait("@patchNotices").then((interception) => {
          const { body } = interception.request;
          const expected = {
            name: newName,
            notice_key: newKey,
            consent_mechanism: notice.consent_mechanism,
            data_uses: notice.data_uses,
            disabled: notice.disabled,
            enforcement_level: notice.enforcement_level,
            has_gpc_flag: notice.has_gpc_flag,
            translations: notice.translations,
            children: [],
          };
          expect(body).to.eql(expected);
        });
        cy.wait("@getNoticeDetail");
      });
    });

    it("can link other notices as children", () => {
      cy.intercept("PATCH", "/api/v1/privacy-notice/*", {}).as("patchNotices");
      cy.fixture("privacy-notices/notice.json").then((notice) => {
        cy.visit(`${PRIVACY_NOTICES_ROUTE}/${ESSENTIAL_NOTICE_ID}`);
        cy.wait("@getNoticeDetail");

        cy.getByTestId("add-children").click();
        cy.getByTestId("select-children").click();
        cy.get(".select-children__menu")
          .find(".select-children__option")
          .first()
          .click();

        cy.getByTestId("save-btn").click();
        cy.wait("@patchNotices").then((interception) => {
          const { body } = interception.request;
          console.log(interception.request);
          const expectedChildren = [
            {
              id: "pri_b1244715-2adb-499f-abb2-e86b6c0040c2",
              name: "Data Sales and Sharing",
            },
          ];
          expect(body.children).to.eql(expectedChildren);
        });
        cy.wait("@getNoticeDetail");
      });
    });
  });

  describe("new privacy notice", () => {
    beforeEach(() => {
      stubPrivacyNoticesCrud();
      stubTaxonomyEntities();
      stubLanguages();
    });

    it("can create a new privacy notice", () => {
      stubTranslationConfig(true);
      cy.visit(`${PRIVACY_NOTICES_ROUTE}/new`);
      cy.getByTestId("new-privacy-notice-page");
      const notice = {
        name: "my notice",
        consent_mechanism: "opt_in",
        enforcement_level: "frontend",
        has_gpc_flag: true,
        data_uses: ["analytics"],
        notice_key: "my_notice",
        disabled: true,
        children: [],
        translations: [
          {
            language: "en",
            title: "Title",
            description: "Some description",
          },
          {
            language: "fr",
            title: "Le titre",
            description: "Un description français",
          },
        ],
      };

      // details section
      cy.getByTestId("input-name").type(notice.name);

      // consent mechanism section
      cy.selectOption("input-consent_mechanism", "Opt in");
      cy.getByTestId("input-has_gpc_flag").click();

      // configuration section
      cy.selectOption("input-data_uses", notice.data_uses[0]);

      // translations
      cy.getByTestId("input-translations.0.title").type("Title");
      cy.getByTestId("input-translations.0.description").type(
        "Some description",
      );

      // add a new translation
      cy.getByTestId("add-language-btn").click();
      cy.getByTestId("select-language").click();
      cy.get(".select-language__menu").find(".select-language__option").click();
      cy.getByTestId("input-translations.1.title").type("Le titre");
      cy.getByTestId("input-translations.1.description").type(
        "Un description français",
      );

      cy.getByTestId("save-btn").click();
      cy.wait("@postNotices").then((interception) => {
        const { body } = interception.request;
        expect(body).to.eql(notice);
      });
      cy.wait("@getNotices");
    });

    it("should dynamically create a notice key", () => {
      cy.visit(`${PRIVACY_NOTICES_ROUTE}/new`);
      cy.getByTestId("new-privacy-notice-page");
      const expected = [
        { name: "Sales", key: "sales" },
        { name: "Data Sales", key: "data_sales" },
        { name: "Data Sales and stuff", key: "data_sales_and_stuff" },
        { name: "Data Sales!!!!", key: "data_sales" },
      ];
      expected.forEach(({ name, key }) => {
        cy.getByTestId("input-name").clear().type(name);
        cy.getByTestId("input-notice_key").should("have.value", key);
      });

      // can still edit the notice key field to be something else
      cy.getByTestId("input-notice_key").clear().type("custom_key");
    });
  });

  describe("translation interface", () => {
    it("shows the translation interface when translations are enabled", () => {
      stubLanguages();
      stubTranslationConfig(true);
      stubTaxonomyEntities();
      cy.visit(`${PRIVACY_NOTICES_ROUTE}/new`);
      cy.wait("@getTranslationConfig");
      cy.getByTestId("add-language-btn").should("exist");
    });

    it("doesn't show the translation interface when translations are disabled", () => {
      stubTranslationConfig(false);
      stubTaxonomyEntities();
      cy.visit(`${PRIVACY_NOTICES_ROUTE}/new`);
      cy.wait("@getTranslationConfig");
      cy.getByTestId("add-language-btn").should("not.exist");
    });
  });
});
