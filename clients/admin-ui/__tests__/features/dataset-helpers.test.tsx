import {
  getUpdatedCollectionFromField,
  getUpdatedDatasetFromClassifyDataset,
  getUpdatedDatasetFromCollection,
  getUpdatedDatasetFromField,
  removeCollectionFromDataset,
  removeFieldFromDataset,
} from "~/features/dataset/helpers";
import {
  mockClassification,
  mockClassifyCollection,
  mockClassifyDataset,
  mockClassifyField,
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
          mockDatasetCollection(),
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

    it("should update a Dataset from a ClassifyInstance", () => {
      const originalDataset = mockDataset({
        collections: [
          mockDatasetCollection({
            name: "users",
            fields: [
              // Field without data categories:
              mockDatasetField({
                name: "email",
                data_categories: [],
              }),
              // Field with data categories:
              mockDatasetField({
                name: "state",
                data_categories: ["system.operations"],
              }),
              // Field without a corresponding classify field:
              mockDatasetField({
                name: "shoe_size",
                data_categories: [],
              }),
            ],
          }),
        ],
      });
      const classifyDataset = mockClassifyDataset({
        collections: [
          mockClassifyCollection({
            name: "users",
            fields: [
              mockClassifyField({
                name: "email",
                classifications: [
                  mockClassification({
                    label: "user.contact",
                    aggregated_score: 0.75,
                  }),
                  mockClassification({
                    label: "user.email",
                    aggregated_score: 0.95,
                  }),
                ],
              }),
              mockClassifyField({
                name: "state",
                classifications: [
                  mockClassification({
                    label: "user.address",
                  }),
                ],
              }),
            ],
          }),
        ],
      });

      const updatedDataset = getUpdatedDatasetFromClassifyDataset(
        originalDataset,
        classifyDataset,
        classifyDataset.collections[0].name,
      );

      // It should return a new object.
      expect(updatedDataset).not.toBe(originalDataset);
      // A field without any categories should be filled in with the high score suggestion.
      expect(updatedDataset.collections[0].fields[0].data_categories).toEqual([
        "user.email",
      ]);
      // A field that already has a category should be unchanged.
      expect(updatedDataset.collections[0].fields[1].data_categories).toEqual([
        "system.operations",
      ]);
      // A field that had no classification match should be unchanged.
      expect(updatedDataset.collections[0].fields[2].data_categories).toEqual(
        [],
      );
    });
  });

  describe("removing from datasets", () => {
    it("should be able to remove a dataset field", () => {
      const deleteName = "remove me";
      const fieldToBeRemoved = mockDatasetField({ name: deleteName });
      const collection = mockDatasetCollection({
        fields: [mockDatasetField(), fieldToBeRemoved, mockDatasetField()],
      });
      const dataset = mockDataset({
        collections: [
          mockDatasetCollection(),
          mockDatasetCollection(),
          collection,
        ],
      });
      const fieldIndex = 1;
      const collectionIndex = 2;
      const updatedDataset = removeFieldFromDataset(
        dataset,
        collectionIndex,
        fieldIndex,
      );

      expect(updatedDataset.collections[collectionIndex].fields).toHaveLength(
        2,
      );
      expect(
        updatedDataset.collections[collectionIndex].fields.filter(
          (f) => f.name === deleteName,
        ),
      ).toHaveLength(0);
    });

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
