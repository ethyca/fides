import * as React from "react";

import ClassifiedDataCategoryInput from "~/features/dataset/ClassifiedDataCategoryInput";
import { MOCK_DATA_CATEGORIES } from "~/mocks/data";
import { DataCategory } from "~/types/api";

const CATEGORIES_WITH_CONFIDENCE = MOCK_DATA_CATEGORIES.map((dc) => ({
  ...dc,
  confidence: Math.floor(Math.random() * 100),
}));
const MOST_LIKELY_CATEGORIES = CATEGORIES_WITH_CONFIDENCE.slice(0, 5);

describe("ClassifiedDataCategoryInput", () => {
  it("can render checked categories", () => {
    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    const selectedClassifiedCategory = MOST_LIKELY_CATEGORIES[0];
    cy.mount(
      <ClassifiedDataCategoryInput
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
      selectedClassifiedCategory.name
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

  it("can select from classified select without overriding taxonomy dropdown", () => {
    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    const toSelect = MOST_LIKELY_CATEGORIES[0];
    cy.mount(
      <ClassifiedDataCategoryInput
        dataCategories={MOCK_DATA_CATEGORIES as DataCategory[]}
        checked={["system.authentication"]}
        onChecked={onCheckedSpy}
        mostLikelyCategories={MOST_LIKELY_CATEGORIES}
      />
    );
    cy.getByTestId("classified-select").click().type(`${toSelect.name}{enter}`);
    cy.get("@onCheckedSpy").should("have.been.calledWith", [
      "system.authentication",
      toSelect.fides_key,
    ]);
  });

  it("can select from taxonomy dropdown without overriding classified select", () => {
    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    const selectedClassifiedCategory = MOST_LIKELY_CATEGORIES[0];
    cy.mount(
      <ClassifiedDataCategoryInput
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
});
