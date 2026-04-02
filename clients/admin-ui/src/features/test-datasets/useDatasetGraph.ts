import { Edge, Node } from "@xyflow/react";
import { useMemo } from "react";

import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

import { buildProtectedPathsByCollection } from "./helpers";

export const DATASET_ROOT_ID = "dataset-root";
export const COLLECTION_ROOT_PREFIX = "collection-";

export type CollectionNodeData = {
  label: string;
  collection: DatasetCollection;
  nodeType: "collection";
  isProtected?: boolean;
  isRoot?: boolean;
  isHighlighted?: boolean;
  filteredFieldCount?: number;
  [key: string]: unknown;
};

export type FieldNodeData = {
  label: string;
  field: DatasetField;
  collectionName: string;
  fieldPath: string;
  nodeType: "field";
  isProtected?: boolean;
  hasChildren: boolean;
  isHighlighted?: boolean;
  [key: string]: unknown;
};

export interface ProtectedFieldsInfo {
  immutable_fields: string[];
  protected_collection_fields: Array<{
    collection: string;
    field: string;
  }>;
}

/**
 * Check if a data category matches any of the filter categories.
 * Treats filter categories as prefixes: selecting "user" matches
 * "user", "user.contact", "user.contact.address.city", etc.
 */
const categoryMatchesFilter = (
  fieldCategory: string,
  filterCategories: string[],
): boolean =>
  filterCategories.some(
    (filter) =>
      fieldCategory === filter || fieldCategory.startsWith(`${filter}.`),
  );

/**
 * Recursively check if a field or any of its descendants have any of the given categories.
 */
const fieldMatchesCategories = (
  field: DatasetField,
  categories: string[],
): boolean => {
  if (
    field.data_categories?.some((c) => categoryMatchesFilter(c, categories))
  ) {
    return true;
  }
  return (
    field.fields?.some((child) => fieldMatchesCategories(child, categories)) ??
    false
  );
};

/**
 * Count top-level fields in a collection that match the filter (or have matching descendants).
 */
const countMatchingFields = (
  collection: DatasetCollection,
  categories: string[],
): number =>
  collection.fields?.filter((f) => fieldMatchesCategories(f, categories))
    .length ?? 0;

/**
 * Check if a collection has any field (recursively) matching any of the given categories.
 */
const collectionMatchesCategories = (
  collection: DatasetCollection,
  categories: string[],
): boolean =>
  collection.fields?.some((f) => fieldMatchesCategories(f, categories)) ??
  false;

/**
 * Recursively build nodes and edges for a field and its nested sub-fields.
 */
const buildFieldNodes = (
  fields: DatasetField[],
  parentId: string,
  collectionName: string,
  pathPrefix: string,
  protectedPaths: Set<string>,
  categoryFilter: string[],
  nodes: Node[],
  edges: Edge[],
) => {
  (Array.isArray(fields) ? fields : []).filter(Boolean).forEach((field) => {
    const fieldPath = pathPrefix ? `${pathPrefix}.${field.name}` : field.name;
    const nodeId = `field-${collectionName}-${fieldPath}`;
    const hasChildren = !!(field.fields && field.fields.length > 0);

    // When filtering by category, skip fields that don't match (including descendants)
    if (
      categoryFilter.length > 0 &&
      !fieldMatchesCategories(field, categoryFilter)
    ) {
      return;
    }

    nodes.push({
      id: nodeId,
      position: { x: 0, y: 0 },
      type: "datasetFieldNode",
      data: {
        label: field.name,
        field,
        collectionName,
        fieldPath,
        nodeType: "field",
        isProtected: protectedPaths.has(fieldPath),
        hasChildren,
      } satisfies FieldNodeData,
    });

    edges.push({
      id: `${parentId}->${nodeId}`,
      source: parentId,
      target: nodeId,
      type: "datasetTreeEdge",
    });

    if (field.fields?.length) {
      buildFieldNodes(
        field.fields,
        nodeId,
        collectionName,
        fieldPath,
        protectedPaths,
        categoryFilter,
        nodes,
        edges,
      );
    }
  });
};

/**
 * Collect all unique data categories from a dataset (all collections and fields recursively).
 */
export const collectDatasetCategories = (dataset: Dataset): string[] => {
  const categories = new Set<string>();

  const walkFields = (fields: DatasetField[]) => {
    (fields ?? []).filter(Boolean).forEach((field) => {
      field.data_categories?.forEach((c) => categories.add(c));
      if (field.fields?.length) {
        walkFields(field.fields);
      }
    });
  };

  (dataset.collections ?? []).filter(Boolean).forEach((collection) => {
    collection.data_categories?.forEach((c) => categories.add(c));
    walkFields(collection.fields ?? []);
  });

  return Array.from(categories).sort();
};

/**
 * Convert a Dataset into React Flow nodes and edges for visualization.
 *
 * When `focusedCollection` is null, shows the overview: root → collection nodes.
 * When `focusedCollection` is set, shows drill-down: collection root → field nodes.
 * When `categoryFilter` is set, hides nodes that don't have any of the specified categories.
 */
const useDatasetGraph = (
  dataset: Dataset | undefined,
  protectedFields?: ProtectedFieldsInfo,
  focusedCollection?: string | null,
  categoryFilter?: string[],
) => {
  return useMemo(() => {
    if (!dataset) {
      return { nodes: [], edges: [] };
    }

    const nodes: Node[] = [];
    const edges: Edge[] = [];
    const filter = categoryFilter ?? [];

    // Build protected paths lookup per collection
    const protectedByCollection = protectedFields
      ? buildProtectedPathsByCollection(
          protectedFields.protected_collection_fields,
        )
      : new Map<string, Set<string>>();

    if (focusedCollection) {
      // --- Drill-down view: single collection → its fields ---
      const collection = (
        Array.isArray(dataset.collections) ? dataset.collections : []
      )
        .filter(Boolean)
        .find((c) => c.name === focusedCollection);
      if (!collection) {
        return { nodes: [], edges: [] };
      }

      const collectionId = `${COLLECTION_ROOT_PREFIX}${collection.name}`;
      const protectedPaths =
        protectedByCollection.get(collection.name) ?? new Set<string>();

      // Collection as root of this view
      nodes.push({
        id: collectionId,
        position: { x: 0, y: 0 },
        type: "datasetCollectionNode",
        data: {
          label: collection.name,
          collection,
          nodeType: "collection",
          isProtected: false,
          isRoot: true,
          ...(filter.length > 0 && {
            filteredFieldCount: countMatchingFields(collection, filter),
          }),
        } satisfies CollectionNodeData,
      });

      buildFieldNodes(
        collection.fields,
        collectionId,
        collection.name,
        "",
        protectedPaths,
        filter,
        nodes,
        edges,
      );
    } else {
      // --- Overview: root → collections only ---
      nodes.push({
        id: DATASET_ROOT_ID,
        position: { x: 0, y: 0 },
        type: "datasetRootNode",
        data: {
          label: dataset.name || dataset.fides_key,
        },
      });

      (Array.isArray(dataset.collections) ? dataset.collections : [])
        .filter(Boolean)
        .forEach((collection) => {
          // In overview mode, hide collections that have no matching fields
          if (
            filter.length > 0 &&
            !collectionMatchesCategories(collection, filter)
          ) {
            return;
          }

          const collectionId = `${COLLECTION_ROOT_PREFIX}${collection.name}`;

          nodes.push({
            id: collectionId,
            position: { x: 0, y: 0 },
            type: "datasetCollectionNode",
            data: {
              label: collection.name,
              collection,
              nodeType: "collection",
              isProtected: false,
              ...(filter.length > 0 && {
                filteredFieldCount: countMatchingFields(collection, filter),
              }),
            } satisfies CollectionNodeData,
          });

          edges.push({
            id: `${DATASET_ROOT_ID}->${collectionId}`,
            source: DATASET_ROOT_ID,
            target: collectionId,
            type: "datasetTreeEdge",
          });
        });
    }

    return { nodes, edges };
  }, [dataset, protectedFields, focusedCollection, categoryFilter]);
};

export default useDatasetGraph;
