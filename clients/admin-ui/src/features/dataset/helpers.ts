import { Dataset, DatasetCollection, DatasetField } from "./types";

export const getUpdatedDatasetCollection = (
  dataset: Dataset,
  collection: DatasetCollection
) => {
  const updatedDataset = { ...dataset };
  const idx = dataset.collections.map((c) => c.name).indexOf(collection.name);
  if (idx !== -1) {
    updatedDataset.collections[idx] = collection;
  }
  return updatedDataset;
};

export const getUpdatedCollectionField = (
  collection: DatasetCollection,
  field: DatasetField
) => {
  const updatedCollection = { ...collection };
  const idx = collection.fields.map((f) => f.name).indexOf(field.name);
  if (idx !== -1) {
    updatedCollection.fields[idx] = field;
  }
  return updatedCollection;
};
