import {
  getUpdatedCollectionField,
  //   getUpdatedDatasetCollection,
} from "~/features/dataset/helpers";
import { mockDatasetCollection, mockDatasetField } from "~/mocks/data";

describe("dataset helpers", () => {
  it("should update a dataset collection", () => {
    const newName = "a fancy email";
    const originalField = mockDatasetField();
    const newField = { ...originalField, ...{ name: newName } };
    const collection = mockDatasetCollection({ fields: [originalField] });
    expect(collection.fields[0].name).toEqual("created_at");

    const updatedCollection = getUpdatedCollectionField(collection, newField);
    expect(updatedCollection.fields[0].name).toEqual(newName);
  });
});
