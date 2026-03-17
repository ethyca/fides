import { Edge, Node } from "@xyflow/react";
import { useMemo } from "react";

import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

export const DATASET_ROOT_ID = "dataset-root";
export const COLLECTION_ROOT_PREFIX = "collection-";

export type CollectionNodeData = {
  label: string;
  collection: DatasetCollection;
  nodeType: "collection";
  isProtected?: boolean;
  isRoot?: boolean;
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
 * Recursively build nodes and edges for a field and its nested sub-fields.
 */
const buildFieldNodes = (
  fields: DatasetField[],
  parentId: string,
  collectionName: string,
  pathPrefix: string,
  protectedPaths: Set<string>,
  nodes: Node[],
  edges: Edge[],
) => {
  fields.forEach((field) => {
    const fieldPath = pathPrefix ? `${pathPrefix}.${field.name}` : field.name;
    const nodeId = `field-${collectionName}-${fieldPath}`;
    const hasChildren = !!(field.fields && field.fields.length > 0);

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
        nodes,
        edges,
      );
    }
  });
};

/**
 * Convert a Dataset into React Flow nodes and edges for visualization.
 *
 * When `focusedCollection` is null, shows the overview: root → collection nodes.
 * When `focusedCollection` is set, shows drill-down: collection root → field nodes.
 */
const useDatasetGraph = (
  dataset: Dataset | undefined,
  protectedFields?: ProtectedFieldsInfo,
  focusedCollection?: string | null,
) => {
  return useMemo(() => {
    if (!dataset) {
      return { nodes: [], edges: [] };
    }

    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Build protected paths lookup per collection
    const protectedByCollection = new Map<string, Set<string>>();
    if (protectedFields) {
      protectedFields.protected_collection_fields.forEach((pf) => {
        if (!protectedByCollection.has(pf.collection)) {
          protectedByCollection.set(pf.collection, new Set());
        }
        const pathSet = protectedByCollection.get(pf.collection)!;
        const segments = pf.field.split(".");
        segments.forEach((_, idx) => {
          pathSet.add(segments.slice(0, idx + 1).join("."));
        });
      });
    }

    if (focusedCollection) {
      // --- Drill-down view: single collection → its fields ---
      const collection = dataset.collections.find(
        (c) => c.name === focusedCollection,
      );
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
        } satisfies CollectionNodeData,
      });

      buildFieldNodes(
        collection.fields,
        collectionId,
        collection.name,
        "",
        protectedPaths,
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

      dataset.collections.forEach((collection) => {
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
  }, [dataset, protectedFields, focusedCollection]);
};

export default useDatasetGraph;
