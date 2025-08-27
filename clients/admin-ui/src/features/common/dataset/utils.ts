import { DatasetField } from "~/types/api";

// Constants for field reference formatting
export const DATASET_REFERENCE_SEPARATOR = ":";
export const FIELD_PATH_SEPARATOR = ".";

/**
 * Builds a field reference string in the format: datasetKey:collectionName:fieldPath
 * @param datasetKey - The dataset's fides_key
 * @param collectionName - The collection name
 * @param fieldPath - The field path (can be nested with dots)
 * @returns The complete field reference string
 */
export const buildFieldReference = (
  datasetKey: string,
  collectionName: string,
  fieldPath: string,
): string => {
  return [datasetKey, collectionName, fieldPath].join(
    DATASET_REFERENCE_SEPARATOR,
  );
};

/**
 * Parses a field reference string back into its components
 * @param reference - The field reference string
 * @returns Object with datasetKey, collectionName, and fieldPath
 */
export const parseFieldReference = (reference: string) => {
  const [datasetKey, collectionName, fieldPath] = reference.split(
    DATASET_REFERENCE_SEPARATOR,
  );
  return { datasetKey, collectionName, fieldPath };
};

/**
 * Transforms dataset fields into tree nodes with proper nesting
 * @param fields - Array of dataset fields
 * @param datasetKey - The dataset's fides_key
 * @param collectionName - The collection name
 * @param parentPath - The parent field path (for nested fields)
 * @returns Array of tree node data for TreeSelect
 */
export const transformFieldsToTreeNodes = (
  fields: DatasetField[],
  datasetKey: string,
  collectionName: string,
  parentPath: string = "",
): DatasetTreeNode[] => {
  return fields.map((field) => {
    const currentPath = parentPath
      ? `${parentPath}${FIELD_PATH_SEPARATOR}${field.name}`
      : field.name;
    const fullReference = buildFieldReference(
      datasetKey,
      collectionName,
      currentPath,
    );
    const hasNestedFields = field.fields && field.fields.length > 0;

    return {
      key: fullReference,
      title: field.name,
      fullTitle: `${collectionName}${DATASET_REFERENCE_SEPARATOR}${currentPath}`,
      value: fullReference,
      isLeaf: !hasNestedFields,
      selectable: true, // Fields are always selectable
      children: hasNestedFields
        ? transformFieldsToTreeNodes(
            field.fields!,
            datasetKey,
            collectionName,
            currentPath,
          )
        : undefined,
    };
  });
};

// Tree node interface for better type safety
export interface DatasetTreeNode {
  key: string;
  title: string;
  fullTitle: string;
  value: string;
  isLeaf: boolean;
  selectable: boolean;
  children?: DatasetTreeNode[];
}

/**
 * Updates tree data by adding children to a specific node
 * @param treeData - Current tree data
 * @param nodeKey - Key of the node to update
 * @param children - New children to add
 * @returns Updated tree data
 */
export const updateTreeNodeChildren = (
  treeData: DatasetTreeNode[],
  nodeKey: string,
  children: DatasetTreeNode[],
): DatasetTreeNode[] => {
  return treeData.map((node) => {
    if (node.key === nodeKey) {
      return { ...node, children };
    }
    if (node.children) {
      return {
        ...node,
        children: updateTreeNodeChildren(node.children, nodeKey, children),
      };
    }
    return node;
  });
};
