import {
  stubPlus,
  stubPrivacyNoticesCrud,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

const DATA_SALES_NOTICE_ID = "pri_afd25287-cce4-487a-a6b4-b7647b068990";
const ESSENTIAL_NOTICE_ID = "pri_e76cbe20-6ffa-46b4-9a91-b1ae3412dd49";

describe("Privacy notices", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/privacy-notice*", {
      fixture: "privacy-notices/list.json",
    }).as("getNotices");
    stubPlus(true);
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
          cy.getByTestId("row-Essential").click();
          // we should still be on the same page
          cy.getByTestId("privacy-notice-detail-page").should("not.exist");
          cy.getByTestId("privacy-notices-page");
        }
      );
    });

    it("viewers and approvers cannot toggle the enable toggle", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_NOTICES_ROUTE);
          cy.wait("@getNotices");
          cy.getByTestId("toggle-Enable")
            .first()
            .within(() => {
              cy.get("span").should("have.attr", "data-disabled");
            });
        }
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
        }
      );
    });
  });

  it("can show an empty state", () => {
    cy.intercept("GET", "/api/v1/privacy-notice*", {
      body: { items: [], page: 1, size: 10, total: 0 },
    }).as("getEmptyNotices");
    cy.visit(PRIVACY_NOTICES_ROUTE);
    cy.wait("@getEmptyNotices");
    cy.getByTestId("empty-state");
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
        "Advertising",
        "Data Sales",
      ].forEach((name) => {
        cy.getByTestId(`row-${name}`);
      });
    });

    it("can sort", () => {
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
        fixture: "privacy-notices/notice_only.json",
      }).as("getNoticeDetail");
      cy.getByTestId("row-Essential").click();
      cy.wait("@getNoticeDetail");
      cy.getByTestId("privacy-notice-detail-page");
      cy.url().should("contain", ESSENTIAL_NOTICE_ID);
    });

    it("can click add button to get to a new form", () => {
      cy.getByTestId("add-privacy-notice-btn").click();
      cy.url().should("contain", `${PRIVACY_NOTICES_ROUTE}/new`);
    });

    describe("enabling and disabling", () => {
      beforeEach(() => {
        cy.intercept("PATCH", "/api/v1/privacy-notice*", {
          fixture: "privacy-notices/list.json",
        }).as("patchNotices");
      });

      it("can enable a notice", () => {
        cy.getByTestId("row-Data Sales").within(() => {
          cy.getByTestId("toggle-Enable").within(() => {
            cy.get("span").should("not.have.attr", "data-checked");
          });
          cy.getByTestId("toggle-Enable").click();
        });

        cy.wait("@patchNotices").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql([{ id: DATA_SALES_NOTICE_ID, disabled: false }]);
        });
        // redux should requery after invalidation
        cy.wait("@getNotices");
      });

      it("can disable a notice with a warning", () => {
        cy.getByTestId("row-Essential").within(() => {
          cy.getByTestId("toggle-Enable").within(() => {
            cy.get("span").should("have.attr", "data-checked");
          });
          cy.getByTestId("toggle-Enable").click();
        });

        cy.getByTestId("confirmation-modal");
        cy.getByTestId("continue-btn").click();
        cy.wait("@patchNotices").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql([{ id: ESSENTIAL_NOTICE_ID, disabled: true }]);
        });
        // redux should requery after invalidation
        cy.wait("@getNotices");
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
      cy.fixture("privacy-notices/notice_only.json").then((notice) => {
        // details section
        cy.getByTestId("input-name").should("have.value", notice.name);
        cy.getByTestId("input-description").should(
          "have.value",
          notice.description
        );

        // consent mechanism section
        cy.getSelectValueContainer("input-consent_mechanism").contains(
          "Notice only"
        );
        cy.getSelectValueContainer("input-enforcement_level").contains(
          "Not applicable"
        );
        cy.getByTestId("input-has_gpc_flag").within(() => {
          cy.get("span").should("not.have.attr", "data-checked");
        });

        // configuration section
        notice.data_uses.forEach((dataUse) => {
          cy.getSelectValueContainer("input-data_uses").contains(dataUse);
        });
        cy.getByTestId("input-internal_description").should("have.value", "");
        notice.regions.forEach((region) => {
          cy.getSelectValueContainer("input-regions").contains(region);
        });
        [
          "displayed_in_overlay",
          "displayed_in_api",
          "displayed_in_privacy_center",
        ].forEach((displayConfig) => {
          cy.getByTestId(`input-${displayConfig}`).within(() => {
            cy.get("span").should("have.attr", "data-checked");
          });
        });
      });
    });

    it("can make an edit", () => {
      cy.visit(`${PRIVACY_NOTICES_ROUTE}/${ESSENTIAL_NOTICE_ID}`);
      cy.wait("@getNoticeDetail");
      const newName = "new name";
      cy.getByTestId("input-name").clear().type(newName);

      cy.getByTestId("save-btn").click();
      cy.wait("@patchNotices").then((interception) => {
        const { body } = interception.request;
        expect(body[0].name).to.eql(newName);
      });
      cy.wait("@getNoticeDetail");
    });
  });

  describe("new privacy notice", () => {
    beforeEach(() => {
      stubPrivacyNoticesCrud();
      stubTaxonomyEntities();
    });

    it("should disable certain fields when notice is notice_only", () => {
      cy.visit(`${PRIVACY_NOTICES_ROUTE}/new`);
      cy.selectOption("input-consent_mechanism", "Notice only");
      cy.getSelectValueContainer("input-enforcement_level").within(() => {
        cy.get("input").should("be.disabled");
      });
      cy.getByTestId("input-has_gpc_flag").within(() => {
        cy.get("span").should("have.attr", "data-disabled");
      });

      // fields should not be disabled otherwise
      cy.selectOption("input-consent_mechanism", "Opt in");
      cy.getSelectValueContainer("input-enforcement_level").within(() => {
        cy.get("input").should("not.be.disabled");
      });
      cy.getByTestId("input-has_gpc_flag").within(() => {
        cy.get("span").should("not.have.attr", "data-disabled");
      });
    });

    it("can create a new privacy notice", () => {
      cy.visit(`${PRIVACY_NOTICES_ROUTE}/new`);
      cy.getByTestId("new-privacy-notice-page");
      const notice = {
        name: "my notice",
        description: "my description",
        consent_mechanism: "opt_in",
        enforcement_level: "system_wide",
        has_gpc_flag: true,
        data_uses: ["advertising"],
        internal_description: "our very important notice, do not touch",
        regions: ["us_ca"],
        displayed_in_privacy_center: true,
        displayed_in_api: false,
        displayed_in_overlay: true,
      };

      // details section
      cy.getByTestId("input-name").type(notice.name);
      cy.getByTestId("input-description").type(notice.description);

      // consent mechanism section
      cy.selectOption("input-consent_mechanism", "Opt in");
      cy.selectOption("input-enforcement_level", "System wide");
      cy.getByTestId("input-has_gpc_flag").click();

      // configuration section
      cy.selectOption("input-data_uses", notice.data_uses[0]);
      cy.getByTestId("input-internal_description").type(
        notice.internal_description
      );
      cy.selectOption("input-regions", notice.regions[0]);
      cy.getByTestId("input-displayed_in_api").click();

      cy.getByTestId("save-btn").click();
      cy.wait("@postNotices").then((interception) => {
        const { body } = interception.request;
        expect(body[0]).to.eql(notice);
      });
      cy.wait("@getNotices");
    });
  });
});
