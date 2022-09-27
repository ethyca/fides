/**
 * Because there is only one /dataset endpoint which handles dataset, collection,
 * and field modifications, and always takes a whole dataset object, it is convenient
 * to have helper functions which, given a field or collection, recreates the
 * entire dataset object to send to the backend.
 *
 * Right now, there are no guaranteed unique attributes on a field or collection, and
 * so we have to use their index in the array. If they ever get a unique ID, we should
 * use that instead.
 */

import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

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

export const removeFieldFromDataset = (
  dataset: Dataset,
  collectionIndex: number,
  fieldIndex: number
): Dataset => {
  const collection = dataset.collections[collectionIndex];
  const newFields = collection.fields.filter((f, idx) => idx !== fieldIndex);
  const updatedCollection = { ...collection, ...{ fields: newFields } };
  return getUpdatedDatasetFromCollection(
    dataset,
    updatedCollection,
    collectionIndex
  );
};

export const removeCollectionFromDataset = (
  dataset: Dataset,
  collectionIndex: number
): Dataset => {
  const newCollections = dataset.collections.filter(
    (c, idx) => idx !== collectionIndex
  );
  return { ...dataset, ...{ collections: newCollections } };
};
