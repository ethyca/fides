/// <reference types="cypress" />

declare global {
  namespace Cypress {
    interface Chainable {
      getAntSelectOption: (optionLabel: string | number) => Chainable;
      /**
       * Select an option from an Ant Design Select component
       * @param option The label of the option to select or the index of the option
       */
      antSelect: (
        option: string | number,
        clickOptions?: { force?: boolean },
      ) => void;
      /**
       * Clear all options from an Ant Design Select component
       */
      antClearSelect: () => void;
      /**
       * Remove a tag (or selected option in mode="multiple") from an Ant Design Select component
       */
      antRemoveSelectTag: (option: string) => void;
      /**
       * Ant Desitn Select component dropdown is visible
       */
      antSelectDropdownVisible: () => void;

      getAntMenuOption: (optionLabel: string | number) => Chainable;
      /**
       * Select an option from an Ant Design Menu component
       * @param option The label of the option to select or the index of the option
       */
      selectAntMenuOption: (
        optionLabel: string | number,
        clickOptions?: { force?: boolean },
      ) => void;
    }
  }
}

Cypress.Commands.add("getAntSelectOption", (option: string | number) =>
  typeof option === "string"
    ? cy.get(
        `.ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option[title="${option}"]`,
      )
    : cy
        .get(
          `.ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option`,
        )
        .eq(option),
);

Cypress.Commands.add(
  "antSelect",
  {
    prevSubject: "element",
  },
  (subject, option, clickOptions) => {
    cy.get(subject.selector).first().should("have.class", "ant-select");
    cy.get(subject.selector)
      .first()
      .invoke("attr", "class")
      .then((classes) => {
        if (classes.includes("ant-select-disabled")) {
          throw new Error("Cannot select from a disabled Ant Select component");
        }
        if (!classes.includes("ant-select-open")) {
          if (classes.includes("ant-select-multiple")) {
            cy.get(subject.selector).first().find("input").click();
          } else {
            cy.get(subject.selector).first().click(clickOptions);
          }
        }
      });
    cy.antSelectDropdownVisible();
    cy.getAntSelectOption(option).should("be.visible").click(clickOptions);
  },
);

Cypress.Commands.add(
  "antClearSelect",
  {
    prevSubject: "element",
  },
  (subject) => {
    cy.get(subject.selector).should("have.class", "ant-select-allow-clear");
    cy.get(subject.selector).find(".ant-select-clear").click({ force: true });
  },
);

Cypress.Commands.add(
  "antRemoveSelectTag",
  {
    prevSubject: "element",
  },
  (subject, option) => {
    cy.get(subject.selector)
      .find(`.ant-select-selection-item[title="${option}"]`)
      .find(".ant-select-selection-item-remove")
      .click();
  },
);

Cypress.Commands.add("antSelectDropdownVisible", () => {
  cy.get(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").should(
    "be.visible",
  );
});

Cypress.Commands.add("getAntMenuOption", (option: string | number) =>
  typeof option === "string"
    ? cy.get(`li.ant-menu-item`).filter(`:contains("${option}")`)
    : cy.get(`li.ant-menu-item`).eq(option),
);
Cypress.Commands.add(
  "selectAntMenuOption",
  {
    prevSubject: "element",
  },
  (subject, option) =>
    cy.get(subject.selector).getAntMenuOption(option).click(),
);

export {};
