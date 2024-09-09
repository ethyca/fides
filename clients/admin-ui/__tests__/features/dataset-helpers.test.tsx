import {
  getUpdatedCollectionFromField,
  getUpdatedDatasetFromCollection,
  getUpdatedDatasetFromField,
  removeCollectionFromDataset,
} from "~/features/dataset/helpers";
import {
  mockDataset,
  mockDatasetCollection,
  mockDatasetField,
} from "~/mocks/data";

describe("dataset helpers", () => {
  describe("update datasets", () => {
    it("should update a dataset collection from a field", () => {
      const newName = "a fancy email";
      const originalField = mockDatasetField();
      const newField = { ...originalField, ...{ name: newName } };
      const collection = mockDatasetCollection({ fields: [originalField] });
      expect(collection.fields[0].name).toEqual("created_at");

      const updatedCollection = getUpdatedCollectionFromField(
        collection,
        newField,
        0,
      );
      expect(updatedCollection.fields[0].name).toEqual(newName);
    });

    it("should update a dataset from a collection", () => {
      const newDescription = "updated description";
      const originalCollection = mockDatasetCollection();
      const updatedCollection = {
        ...originalCollection,
        ...{ description: newDescription },
      };
      const dataset = mockDataset({ collections: [originalCollection] });
      const updatedDataset = getUpdatedDatasetFromCollection(
        dataset,
        updatedCollection,
        0,
      );
      expect(updatedDataset.collections[0].description).toEqual(newDescription);
    });

    it("should update a dataset from a field", () => {
      const newName = "a fancy email";
      const originalField = mockDatasetField({ name: "a regular email" });

      const newField = { ...originalField, ...{ name: newName } };
      const collection = mockDatasetCollection({
        fields: [
          mockDatasetCollection() as any,
          mockDatasetCollection(),
          mockDatasetCollection({ fields: [originalField] }),
        ],
      });
      const dataset = mockDataset({
        collections: [mockDatasetCollection(), collection],
      });
      const fieldIndex = 2;
      const collectionIndex = 1;
      const updatedDataset = getUpdatedDatasetFromField(
        dataset,
        newField,
        collectionIndex,
        fieldIndex,
      );
      expect(
        updatedDataset.collections[collectionIndex].fields[fieldIndex].name,
      ).toEqual(newName);
    });
  });

  describe("removing from datasets", () => {
    it("should be able to remove a dataset collection", () => {
      const deleteName = "remove me";
      const collection = mockDatasetCollection({ name: deleteName });
      const dataset = mockDataset({
        collections: [
          mockDatasetCollection(),
          collection,
          mockDatasetCollection(),
        ],
      });
      const collectionIndex = 1;
      const updatedDataset = removeCollectionFromDataset(
        dataset,
        collectionIndex,
      );
      expect(updatedDataset.collections).toHaveLength(2);
      expect(
        updatedDataset.collections.filter((f) => f.name === deleteName),
      ).toHaveLength(0);
    });
  });
});
