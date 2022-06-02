import { Dataset, DatasetCollection, DatasetField } from "./types";

export const getUpdatedDatasetFromCollection = (
  dataset: Dataset,
  collection: DatasetCollection,
  collectionIndex: number
) => {
  const newCollections = dataset.collections.map((c, idx) => {
    if (idx === collectionIndex) {
      return collection;
    }
    return c;
  });
  return { ...dataset, ...{ collections: newCollections } };
};

export const getUpdatedCollectionFromField = (
  collection: DatasetCollection,
  field: DatasetField,
  fieldIndex: number
) => {
  const newFields = collection.fields.map((f, idx) => {
    if (idx === fieldIndex) {
      return field;
    }
    return f;
  });
  return { ...collection, ...{ fields: newFields } };
};

export const getUpdatedDatasetFromField = (
  dataset: Dataset,
  field: DatasetField,
  collectionIndex: number,
  fieldIndex: number
) => {
  const collection = dataset.collections[collectionIndex];
  const updatedCollection = getUpdatedCollectionFromField(
    collection,
    field,
    fieldIndex
  );
  return getUpdatedDatasetFromCollection(
    dataset,
    updatedCollection,
    collectionIndex
  );
};
