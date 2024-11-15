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
    }
  }
}

Cypress.Commands.add("getAntSelectOption", (option: string | number) =>
  typeof option === "string"
    ? cy.get(`.ant-select-item-option[title="${option}"]`)
    : cy.get(`.ant-select-item-option`).eq(option),
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
          cy.get(subject.selector).first().click(clickOptions);
        }
      });
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

export {};
