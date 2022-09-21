import * as React from "react";

import ClassifiedDataCategoryInput from "~/features/dataset/ClassifiedDataCategoryInput";
import { MOCK_DATA_CATEGORIES } from "~/mocks/data";
import { DataCategory } from "~/types/api";

const CATEGORIES_WITH_CONFIDENCE = MOCK_DATA_CATEGORIES.map((dc) => ({
  ...dc,
  confidence: Math.floor(Math.random() * 100),
}));

describe("ClassifiedDataCategoryInput", () => {
  it("can check a category", () => {
    const onCheckedSpy = cy.spy().as("onCheckedSpy");
    cy.mount(
      <ClassifiedDataCategoryInput
        dataCategories={MOCK_DATA_CATEGORIES as DataCategory[]}
        checked={["user"]}
        onChecked={onCheckedSpy}
        mostLikelyCategories={CATEGORIES_WITH_CONFIDENCE.slice(0, 5)}
      />
    );
  });
});
