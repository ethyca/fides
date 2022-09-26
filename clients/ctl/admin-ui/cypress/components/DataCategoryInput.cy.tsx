import * as React from "react";

import DataCategoryInput from "~/features/dataset/DataCategoryInput";
import { MOCK_DATA_CATEGORIES } from "~/mocks/data";
import { DataCategory } from "~/types/api";

import { stubPlusHealth } from "../support/stubs";

describe("DataCategoryInput", () => {
  it("can check a category", () => {
    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    cy.mount(
      <DataCategoryInput
        dataCategories={MOCK_DATA_CATEGORIES as DataCategory[]}
        checked={["user"]}
        onChecked={onCheckedSpy}
      />
    );

    cy.getByTestId("classified-select").should("not.exist");

    cy.getByTestId("selected-categories").should("contain", "user");
    cy.getByTestId("data-category-dropdown").click();
    cy.getByTestId("expand-System Data").click();
    cy.getByTestId("checkbox-Authentication Data").click();

    cy.get("@onCheckedSpy").should("have.been.calledWith", [
      "user",
      "system.authentication",
    ]);
  });

  it("can render the classified version", () => {
    stubPlusHealth();

    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    cy.mount(
      <DataCategoryInput
        dataCategories={MOCK_DATA_CATEGORIES as DataCategory[]}
        checked={["user"]}
        onChecked={onCheckedSpy}
      />
    );
    cy.getByTestId("classified-select");
  });
});
