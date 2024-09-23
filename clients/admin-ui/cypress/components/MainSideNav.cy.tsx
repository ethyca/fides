import * as React from "react";

import { UnconnectedMainSideNav } from "~/features/common/nav/v2/MainSideNav";
import {
  configureNavGroups,
  findActiveNav,
  NavConfigGroup,
} from "~/features/common/nav/v2/nav-config";

const ACTIVE_BACKGROUND_COLOR = "rgb(206, 202, 194)";
const INACTIVE_BACKGROUND_COLOR = "rgba(0, 0, 0, 0)";

const selectLinkColor = (title: string) =>
  cy.contains("a", title).should("have.css", "background-color");

const verifyActiveState = ({
  active,
  inactive,
}: {
  active: string[];
  inactive: string[];
}) => {
  active.forEach((title) => {
    selectLinkColor(title).should("eql", ACTIVE_BACKGROUND_COLOR);
  });
  inactive.forEach((title) => {
    selectLinkColor(title).should("eql", INACTIVE_BACKGROUND_COLOR);
  });
};

describe("UnconnectedMainSideNav", () => {
  it("renders children nav links", () => {
    const config: NavConfigGroup[] = [
      {
        title: "Consent",
        routes: [
          {
            title: "Privacy notices",
            path: "/consent/privacy-notices",
            scopes: [],
          },
          {
            title: "Privacy experiences",
            path: "/consent/privacy-experiences",
            scopes: [],
          },
        ],
      },
      {
        title: "Settings",
        routes: [
          {
            title: "Users",
            path: "/users",
            scopes: [],
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
    cy.mount(<UnconnectedMainSideNav groups={navGroups} active={activeNav} />);

    // Renders groups as buttons (for accordion)
    cy.contains("nav button", "Consent");

    // Renders links as links
    cy.contains("nav a", "Privacy notices");
    cy.contains("nav a", "Privacy experiences");
    cy.contains("nav a", "Users");

    verifyActiveState({
      active: ["Privacy notices"],
      inactive: ["Privacy experiences", "Users"],
    });
  });
});
