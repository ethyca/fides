import * as React from "react";

import {
  configureNavGroups,
  findActiveNav,
  NavConfigGroup,
} from "~/features/common/nav/v2/nav-config";
import { UnconnectedNavSideBar } from "~/features/common/nav/v2/NavSideBar";

const ACTIVE_COLOR = "rgb(130, 78, 242)";
const INACTIVE_COLOR = "rgb(45, 55, 72)";

const selectLinkColor = (title: string) =>
  cy.contains("a", title).should("have.css", "color");

const verifyActiveState = ({
  active,
  inactive,
}: {
  active: string[];
  inactive: string[];
}) => {
  active.forEach((title) => {
    selectLinkColor(title).should("eql", ACTIVE_COLOR);
  });
  inactive.forEach((title) => {
    selectLinkColor(title).should("eql", INACTIVE_COLOR);
  });
};

describe("NavSideBar", () => {
  it("renders children nav links", () => {
    const config: NavConfigGroup[] = [
      {
        title: "Privacy requests",
        routes: [
          {
            path: "/privacy-requests",
            scopes: [],
          },
          {
            title: "Consent",
            path: "/consent",
            scopes: [],
            routes: [
              {
                title: "Privacy notices",
                path: "/consent/privacy-notices",
                scopes: [],
                routes: [
                  {
                    title: "3rd level page",
                    path: "/consent/privacy-notices/third-level-page",
                    scopes: [],
                  },
                ],
              },
              {
                title: "Cookies",
                path: "/consent/cookies",
                scopes: [],
              },
            ],
          },
        ],
      },
    ];
    const navGroups = configureNavGroups({
      config,
      userScopes: [],
    });
    const path = "/consent/privacy-notices";
    const activeNav = findActiveNav({ navGroups, path });

    // First check if the active path is /consent/privacy-notices
    cy.mount(
      <UnconnectedNavSideBar
        routerPathname={path}
        groups={navGroups}
        active={activeNav}
      />
    );

    cy.contains("nav li", "Privacy requests");
    cy.contains("nav li", "Consent").within(() => {
      cy.contains("a", "Privacy notices");
      cy.contains("a", "Cookies");
    });

    verifyActiveState({
      active: ["Privacy notices", "Consent"],
      inactive: ["Privacy requests", "3rd level page", "Cookies"],
    });

    // Check if the active path is only on the first level
    cy.mount(
      <UnconnectedNavSideBar
        routerPathname="/consent"
        groups={navGroups}
        active={activeNav}
      />
    );
    verifyActiveState({
      active: ["Consent"],
      inactive: [
        "Privacy notices",
        "Privacy requests",
        "3rd level page",
        "Cookies",
      ],
    });

    // Check if the active path is deeper nested
    cy.mount(
      <UnconnectedNavSideBar
        routerPathname="/consent/privacy-notices/third-level-page"
        groups={navGroups}
        active={activeNav}
      />
    );
    verifyActiveState({
      active: ["Consent", "Privacy notices", "3rd level page"],
      inactive: ["Privacy requests", "Cookies"],
    });
  });
});
