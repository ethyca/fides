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

      /**
       * Get an option from an Ant Design Tabs component by label
       * @param tab The label of the tab to get
       * @example cy.getAntTab("Some tab").click();
       * @example cy.getAntTab("Some tab").should("have.attr", "aria-disabled", "true");
       */
      getAntTab: (tab: string) => Chainable;
      /**
       * Click an option from an Ant Design Tabs component by label
       * @param tab The label of the tab to click
       */
      clickAntTab: (tab: string) => Chainable;

      /**
       * Get a panel from an Ant Design Tabs component by label
       * @param tabKey The key of the tab panel to get
       * @example cy.getAntTabPanel("some-tab-key").should("be.visible");
       */
      getAntTabPanel: (tabKey: string) => Chainable;

      /** Apply a filter to an Ant Design table column
       * @param columnTitle The title of the column to filter
       * @param filterOption The filter option to select (string for specific option, number for index)
       */
      applyTableFilter: (
        columnTitle: string,
        filterOption: string | number,
      ) => void;

      /**
       * Get a row from an Ant Design Table component by row key
       * @param rowKey The key of the row to get
       * @example cy.getAntTableRow("some-row-key").should("be.visible");
       */
      getAntTableRow: (rowKey: string) => Chainable;

      /**
       * Get a cell from an Ant Design Table component by cell index within a row
       * @param cellIndex The index of the cell to get
       * @example cy.getAntTableRow("some-row-key").within(() => {
       *   cy.getAntCellWithinRow(0).should("be.visible");
       * });
       */
      getAntCellWithinRow: (cellIndex: number) => Chainable;

      /**
       * Get the pagination component from an Ant Design Table component
       */
      getAntPagination: () => Chainable;

      /**
       * Click the previous page button in the pagination component
       */
      antPaginatePrevious: () => void;

      /**
       * Click the next page button in the pagination component
       */
      antPaginateNext: () => void;

      /**
       * Get an option from an Ant Design Dropdown component by label
       * @param option The label of the option to get
       * @example cy.getAntDropdownOption("Delete").should("be.visible");
       */
      getAntDropdownOption: (option: string | number) => Chainable;

      /**
       * Select an option from an Ant Design Dropdown component
       * @param option The label of the option to select or the index of the option
       */
      selectAntDropdownOption: (option: string | number) => void;

      /**
       * Pick a dataset and field reference using the DatasetReferencePicker component
       * @param datasetName The name of the dataset to select
       * @param collectionName The name of the collection to expand
       * @param fieldName The name of the field to select
       */
      pickDatasetReference: (
        datasetName: string,
        collectionName: string,
        fieldName: string,
      ) => void;
    }
  }
}

Cypress.Commands.add("getAntSelectOption", (option: string | number) =>
  typeof option === "string"
    ? cy.get(
        `.ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option[title="${option}"]`,
        { withinSubject: null },
      )
    : cy
        .get(
          `.ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option`,
          { withinSubject: null },
        )
        .eq(option),
);

Cypress.Commands.add(
  "antSelect",
  {
    prevSubject: "element",
  },
  (subject, option, clickOptions = { force: true }) => {
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
            cy.get(subject.selector).first().find("input").focus().click();
          } else {
            cy.get(subject.selector)
              .first()
              .find("input")
              .focus()
              .click(clickOptions);
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
  cy.get(".ant-select-dropdown:not(.ant-select-dropdown-hidden)", {
    withinSubject: null,
  }).should("be.visible");
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

Cypress.Commands.add("getAntTab", (tab: string) =>
  cy
    .get("[role='tab'], .ant-menu-horizontal  [role='menuitem']")
    .filter(`:contains("${tab}")`),
);
Cypress.Commands.add("clickAntTab", (tab: string) => {
  cy.getAntTab(tab).click({ force: true });
  cy.getAntTab(tab).should(($tab) => {
    const hasActiveClass = $tab.hasClass("ant-menu-item-selected");
    const parentHasActiveClass = $tab.parent().hasClass("ant-tabs-tab-active");
    expect(hasActiveClass || parentHasActiveClass).to.be.true;
  });
  // eslint-disable-next-line cypress/no-unnecessary-waiting
  cy.wait(500); // Wait for the animation/router to complete
});
Cypress.Commands.add("getAntTabPanel", (tab: string) =>
  cy.get(`#rc-tabs-0-panel-${tab}`),
);
Cypress.Commands.add("applyTableFilter", (columnTitle, filterOption) => {
  // Click the filter trigger for the specified column
  cy.get(".ant-table-column-title")
    .contains(columnTitle)
    .siblings(".ant-dropdown-trigger")
    .click({ force: true });

  // Wait for the filter dropdown to appear and find the visible one
  cy.get(".ant-table-filter-dropdown:visible")
    .should("be.visible")
    .within(() => {
      // Wait for menu items to be available
      cy.get(".ant-dropdown-menu-item").should("have.length.at.least", 1);

      // Select the filter option
      if (typeof filterOption === "string") {
        cy.get(".ant-dropdown-menu-item")
          .contains(filterOption)
          .should("exist")
          .click();
      } else {
        cy.get(".ant-dropdown-menu-item")
          .eq(filterOption)
          .should("exist")
          .click();
      }

      // Click OK to apply the filter
      cy.get(".ant-table-filter-dropdown-btns .ant-btn-primary")
        .should("exist")
        .click();
    });

  // Wait for the dropdown to disappear
  cy.get(".ant-table-filter-dropdown:visible").should("not.exist");
});
Cypress.Commands.add("getAntTableRow", (rowKey: string) =>
  cy.get(`[data-row-key='${rowKey}']`),
);
Cypress.Commands.add("getAntCellWithinRow", (cellIndex: number) =>
  cy.get(`td:not(.ant-table-selection-column)`).eq(cellIndex),
);
Cypress.Commands.add("getAntPagination", () =>
  cy.get(".ant-pagination").first(),
);
Cypress.Commands.add("antPaginatePrevious", () =>
  cy.getAntPagination().find("li.ant-pagination-prev button").click(),
);
Cypress.Commands.add("antPaginateNext", () =>
  cy.getAntPagination().find("li.ant-pagination-next button").click(),
);
Cypress.Commands.add("getAntDropdownOption", (option: string | number) =>
  typeof option === "string"
    ? cy.get(".ant-dropdown-menu-item").contains(option)
    : cy.get(".ant-dropdown-menu-item").eq(option),
);
Cypress.Commands.add("selectAntDropdownOption", (option: string | number) =>
  cy.getAntDropdownOption(option).click({ force: true }),
);

Cypress.Commands.add(
  "pickDatasetReference",
  {
    prevSubject: "element",
  },
  (subject, datasetName: string, collectionName: string, fieldName: string) => {
    // First select the dataset
    cy.get(subject.selector)
      .find("[data-testid='dataset-select']")
      .antSelect(datasetName);

    // Wait for the field tree to load with the selected dataset
    cy.get(subject.selector)
      .find("[data-testid='field-tree-select']")
      .should("not.be.disabled");

    // Then select the field using tree select
    cy.get(subject.selector).find("[data-testid='field-tree-select']").click();

    // Wait for tree dropdown to open
    cy.get(".ant-tree-select-dropdown:not(.ant-tree-select-dropdown-hidden)", {
      withinSubject: null,
    }).should("be.visible");

    // Find the collection and expand it
    cy.get(".ant-select-tree-title", {
      withinSubject: null,
    })
      .contains(collectionName)
      .closest(".ant-select-tree-treenode")
      .find(".ant-select-tree-switcher")
      .click();

    // Wait for the field to become visible after expansion
    cy.get(".ant-select-tree-title", {
      withinSubject: null,
    })
      .contains(fieldName)
      .should("be.visible")
      .click();
  },
);

export {};
