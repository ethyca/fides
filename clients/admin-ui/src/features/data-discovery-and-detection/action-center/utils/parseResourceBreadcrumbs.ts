import { Icons } from "fidesui";

import { StagedResourceTypeValue } from "~/types/api";

import { MAP_DATASTORE_RESOURCE_TYPE_TO_ICON } from "../fields/MonitorFields.const";

const URN_SEPARATOR = ".";

// Map URN depth to resource type for datastore hierarchy
// Depth 0: monitor_id (not included in breadcrumbs)
// Depth 1: Database/Project
// Depth 2: Schema/Dataset
// Depth 3: Table/Collection
// Depth 4+: Field/Column (and nested fields)
const getResourceTypeByDepth = (depth: number): StagedResourceTypeValue => {
  switch (depth) {
    case 1:
      return StagedResourceTypeValue.DATABASE;
    case 2:
      return StagedResourceTypeValue.SCHEMA;
    case 3:
      return StagedResourceTypeValue.TABLE;
    default:
      // 4 or greater = Field/Column (including nested)
      return StagedResourceTypeValue.FIELD;
  }
};

export interface UrnBreadcrumbItem {
  title: string;
  IconComponent?: Icons.CarbonIconType;
}

/**
 * Parses a URN into breadcrumb items without links.
 * Returns the resource hierarchy with appropriate icons based on the abstraction layer.
 * Excludes the last part (field name) as it's typically displayed separately.
 *
 * URN format: monitor_id.database.schema.table.field.nestedField...
 *
 * Examples:
 * - "monitor.db.schema.table" → [db icon, schema icon]
 * - "monitor.db.schema.table.field" → [db icon, schema icon, table icon]
 *
 * @param urn - The URN string to parse
 * @returns Array of breadcrumb items with titles and icons, or empty array if URN is malformed
 */
export const parseResourceBreadcrumbs = (
  urn: string | undefined,
): UrnBreadcrumbItem[] => {
  // Handle null, undefined, or empty string
  if (!urn || typeof urn !== "string") {
    return [];
  }

  // Trim whitespace
  const trimmedUrn = urn.trim();
  if (!trimmedUrn) {
    return [];
  }

  // Split by separator
  const urnParts = trimmedUrn.split(URN_SEPARATOR);

  // Need at least monitor_id + one resource level
  if (urnParts.length < 2) {
    return [];
  }

  // Validate that all parts are non-empty strings
  // Filter out any empty parts that might result from malformed URNs like "monitor..db"
  const validParts = urnParts.filter((part) => part && part.trim().length > 0);

  // Re-validate after filtering
  if (validParts.length < 2) {
    return [];
  }

  // Remove monitor_id (first part)
  validParts.shift();

  // Remove the last part (field name, already displayed separately)
  // Only pop if there's at least one part left
  if (validParts.length > 0) {
    validParts.pop();
  }

  // If no parts remain after removing monitor_id and field name, return empty
  if (validParts.length === 0) {
    return [];
  }

  // Map each part to a breadcrumb with the appropriate icon
  return validParts.map((part, idx) => {
    const depth = idx + 1; // +1 because we removed monitor_id
    const resourceType = getResourceTypeByDepth(depth);
    const IconComponent = MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[resourceType];

    return {
      title: part.trim(),
      IconComponent,
    };
  });
};
