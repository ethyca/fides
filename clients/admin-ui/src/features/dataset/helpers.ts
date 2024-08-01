import produce from "immer";

import {
  Classification,
  ClassifyDataset,
  ClassifyField,
  Dataset,
  DatasetCollection,
  DatasetField,
} from "~/types/api";

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

export const getUpdatedDatasetFromCollection = (
  dataset: Dataset,
  collection: DatasetCollection,
  collectionIndex: number,
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
  fieldIndex: number,
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
  fieldIndex: number,
) => {
  const collection = dataset.collections[collectionIndex];
  const updatedCollection = getUpdatedCollectionFromField(
    collection,
    field,
    fieldIndex,
  );
  return getUpdatedDatasetFromCollection(
    dataset,
    updatedCollection,
    collectionIndex,
  );
};

export const getTopClassification = (
  classifyField: ClassifyField,
): Classification =>
  classifyField.classifications.reduce((maxClassification, next) => {
    if (
      (maxClassification.aggregated_score ?? 0) < (next.aggregated_score ?? 0)
    ) {
      return next;
    }
    return maxClassification;
  });

/**
 * Returns a new dataset object with the top-scoring classification results filling in data
 * categories that were left blank on the dataset. Uses immer to efficiently modify a draft object.
 */
export const getUpdatedDatasetFromClassifyDataset = (
  dataset: Dataset,
  classifyDataset: ClassifyDataset,
  activeCollection: string | undefined,
): Dataset =>
  produce(dataset, (draftDataset) => {
    const classifyCollectionMap = new Map(
      classifyDataset.collections.map((c) => [c.name, c]),
    );

    draftDataset.collections.forEach((draftCollection) => {
      const classifyCollection = classifyCollectionMap.get(
        draftCollection.name,
      );

      if (activeCollection && classifyCollection?.name !== activeCollection) {
        return;
      }

      const classifyFieldMap = new Map(
        classifyCollection?.fields?.map((f) => [f.name, f]),
      );

      draftCollection.fields.forEach((draftField) => {
        if (
          draftField.data_categories &&
          draftField.data_categories.length > 0
        ) {
          return;
        }

        const classifyField = classifyFieldMap.get(draftField.name);
        if (!(classifyField && classifyField.classifications.length > 0)) {
          return;
        }

        const topClassification = getTopClassification(classifyField);

        draftField.data_categories = [topClassification.label];
      });
    });
  });

export const removeFieldFromDataset = (
  dataset: Dataset,
  collectionIndex: number,
  fieldIndex: number,
): Dataset => {
  const collection = dataset.collections[collectionIndex];
  const newFields = collection.fields.filter((f, idx) => idx !== fieldIndex);
  const updatedCollection = { ...collection, ...{ fields: newFields } };
  return getUpdatedDatasetFromCollection(
    dataset,
    updatedCollection,
    collectionIndex,
  );
};

export const removeCollectionFromDataset = (
  dataset: Dataset,
  collectionIndex: number,
): Dataset => {
  const newCollections = dataset.collections.filter(
    (c, idx) => idx !== collectionIndex,
  );
  return { ...dataset, ...{ collections: newCollections } };
};
