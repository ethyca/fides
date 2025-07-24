import { get } from "lodash";

import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

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

export const removeCollectionFromDataset = (
  dataset: Dataset,
  collectionIndex: number,
): Dataset => {
  const newCollections = dataset.collections.filter(
    (c, idx) => idx !== collectionIndex,
  );
  return { ...dataset, ...{ collections: newCollections } };
};

/**
 * Returns the path that can be used to navigate a dataset object.
 * example return values: "collections[0].fields[1]"
 * We can then use the object path to get or update properties in the dataset object
 */

interface GetDatasetPathParams {
  dataset: Dataset;
  collectionName: string;
  subfields?: string[];
}

export const getDatasetPath = ({
  dataset,
  collectionName,
  subfields,
}: GetDatasetPathParams) => {
  let path = "";
  const collectionIndex = dataset.collections.findIndex(
    (collection) => collection.name === collectionName,
  );
  path += `collections[${collectionIndex}]`;

  if (!subfields) {
    return path;
  }

  subfields.forEach((subfieldName) => {
    const field: DatasetField = get(dataset, path);
    const subfieldIndex = field.fields!.findIndex(
      (subfield) => subfield.name === subfieldName,
    );
    path += `.fields[${subfieldIndex}]`;
  });

  return path;
};
