import * as React from "react";

import ClassifiedDataCategoryDropdown from "~/features/dataset/ClassifiedDataCategoryDropdown";
import { MOCK_DATA_CATEGORIES } from "~/mocks/data";
import { DataCategory } from "~/types/api";

const CATEGORIES_WITH_CONFIDENCE = MOCK_DATA_CATEGORIES.map((dc) => ({
  ...dc,
  confidence: Math.random(),
}));
const MOST_LIKELY_CATEGORIES = CATEGORIES_WITH_CONFIDENCE.slice(0, 5);

describe("ClassifiedDataCategoryDropdown", () => {
  it("can render checked categories", () => {
    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    const selectedClassifiedCategory = MOST_LIKELY_CATEGORIES[0];
    cy.mount(
      <ClassifiedDataCategoryDropdown
        dataCategories={MOCK_DATA_CATEGORIES as DataCategory[]}
        // check one "most likely" and one regular one
        checked={[
          selectedClassifiedCategory.fides_key,
          "system.authentication",
        ]}
        onChecked={onCheckedSpy}
        mostLikelyCategories={MOST_LIKELY_CATEGORIES}
      />
    );

    // check that the classified one is selected
    cy.getByTestId("classified-select").should(
      "contain",
      selectedClassifiedCategory.fides_key
    );
    // check that the regular one is selected
    cy.getByTestId("data-category-dropdown").click();
    cy.get("[data-testid='checkbox-Authentication Data'] > span").should(
      "have.attr",
      "data-checked"
    );
    cy.get(
      `[data-testid='checkbox-${selectedClassifiedCategory.name}'] > span`
    ).should("have.attr", "data-checked");
  });

  it("can render all categories even if not recommended", () => {
    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    const selectedClassifiedCategory = MOST_LIKELY_CATEGORIES[0];
    const otherCategory = MOCK_DATA_CATEGORIES[6];
    cy.mount(
      <ClassifiedDataCategoryDropdown
        dataCategories={MOCK_DATA_CATEGORIES as DataCategory[]}
        // check one "most likely" and one regular one
        checked={[
          selectedClassifiedCategory.fides_key,
          "system.authentication",
        ]}
        onChecked={onCheckedSpy}
        mostLikelyCategories={MOST_LIKELY_CATEGORIES}
      />
    );
    cy.getByTestId("classified-select").contains("system.authentication (N/A)");
    cy.getByTestId("classified-select")
      .click()
      .within(() => {
        cy.contains(`${otherCategory.fides_key} (N/A)`);
      });
  });

  it("can select from classified select without overriding taxonomy dropdown", () => {
    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    const toSelect = MOST_LIKELY_CATEGORIES[0];
    cy.mount(
      <ClassifiedDataCategoryDropdown
        dataCategories={MOCK_DATA_CATEGORIES as DataCategory[]}
        checked={["system.authentication"]}
        onChecked={onCheckedSpy}
        mostLikelyCategories={MOST_LIKELY_CATEGORIES}
      />
    );
    cy.getByTestId("classified-select")
      .click()
      .type(`${toSelect.fides_key}{enter}`);
    cy.get("@onCheckedSpy").should("have.been.calledWith", [
      "system.authentication",
      toSelect.fides_key,
    ]);
  });

  it("can select from taxonomy dropdown without overriding classified select", () => {
    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    const selectedClassifiedCategory = MOST_LIKELY_CATEGORIES[0];
    cy.mount(
      <ClassifiedDataCategoryDropdown
        dataCategories={MOCK_DATA_CATEGORIES as DataCategory[]}
        checked={[selectedClassifiedCategory.fides_key]}
        onChecked={onCheckedSpy}
        mostLikelyCategories={MOST_LIKELY_CATEGORIES}
      />
    );
    cy.getByTestId("data-category-dropdown").click();
    cy.getByTestId("expand-System Data").click();
    cy.getByTestId("checkbox-Authentication Data").click();
    cy.get("@onCheckedSpy").should("have.been.calledWith", [
      selectedClassifiedCategory.fides_key,
      "system.authentication",
    ]);
  });

  it("can remove items from classified select", () => {
    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    const selectedClassifiedCategory = MOST_LIKELY_CATEGORIES[0];
    cy.mount(
      <ClassifiedDataCategoryDropdown
        dataCategories={MOCK_DATA_CATEGORIES as DataCategory[]}
        checked={[
          selectedClassifiedCategory.fides_key,
          "system.authentication",
        ]}
        onChecked={onCheckedSpy}
        mostLikelyCategories={MOST_LIKELY_CATEGORIES}
      />
    );
    // delete the selected category
    cy.getByTestId("classified-select").click().type("{backspace}");
    cy.get("@onCheckedSpy").should("have.been.calledWith", [
      selectedClassifiedCategory.fides_key,
    ]);
  });

  it("can remove items from taxonomy select", () => {
    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    const selectedClassifiedCategory = MOST_LIKELY_CATEGORIES[0];
    cy.mount(
      <ClassifiedDataCategoryDropdown
        dataCategories={MOCK_DATA_CATEGORIES as DataCategory[]}
        checked={[
          selectedClassifiedCategory.fides_key,
          "system.authentication",
        ]}
        onChecked={onCheckedSpy}
        mostLikelyCategories={MOST_LIKELY_CATEGORIES}
      />
    );
    // uncheck system authentication
    cy.getByTestId("data-category-dropdown").click();
    cy.getByTestId("checkbox-Authentication Data").click();
    cy.get("@onCheckedSpy").should("have.been.calledWith", [
      selectedClassifiedCategory.fides_key,
    ]);
  });

  it("playground", () => {
    // it's useful when developing to be able to play with the component with actual react state
    const ClassifiedDataCategoryDropdownWithState = () => {
      const [checked, setChecked] = React.useState([]);
      return (
        <ClassifiedDataCategoryDropdown
          dataCategories={MOCK_DATA_CATEGORIES as DataCategory[]}
          checked={checked}
          onChecked={setChecked}
          mostLikelyCategories={MOST_LIKELY_CATEGORIES}
        />
      );
    };
    cy.mount(<ClassifiedDataCategoryDropdownWithState />);
  });
});
