import { ConnectionCategory } from "~/types/api/models/ConnectionCategory";

/**
 * Maps ConnectionCategory enum values to human-readable labels
 */
export const getCategoryLabel = (category: ConnectionCategory): string => {
  switch (category) {
    case ConnectionCategory.DATA_CATALOG:
      return "Data Catalog";
    case ConnectionCategory.DATA_WAREHOUSE:
      return "Data Warehouse";
    case ConnectionCategory.DATABASE:
      return "Database";
    case ConnectionCategory.IDENTITY_PROVIDER:
      return "Identity Provider";
    case ConnectionCategory.WEBSITE:
      return "Website";
    case ConnectionCategory.CRM:
      return "CRM";
    case ConnectionCategory.MANUAL:
      return "Manual";
    case ConnectionCategory.MARKETING:
      return "Marketing";
    case ConnectionCategory.ANALYTICS:
      return "Analytics";
    case ConnectionCategory.ECOMMERCE:
      return "E-commerce";
    case ConnectionCategory.COMMUNICATION:
      return "Communication";
    case ConnectionCategory.CUSTOM:
      return "Custom";
    default:
      return category; // Fallback to enum value
  }
};

/**
 * Maps human-readable labels back to ConnectionCategory enum values
 */
export const getCategoryFromLabel = (
  label: string,
): ConnectionCategory | null => {
  const labelMap: Record<string, ConnectionCategory> = {
    "Data Catalog": ConnectionCategory.DATA_CATALOG,
    "Data Warehouse": ConnectionCategory.DATA_WAREHOUSE,
    Database: ConnectionCategory.DATABASE,
    "Identity Provider": ConnectionCategory.IDENTITY_PROVIDER,
    Website: ConnectionCategory.WEBSITE,
    CRM: ConnectionCategory.CRM,
    Manual: ConnectionCategory.MANUAL,
    Marketing: ConnectionCategory.MARKETING,
    Analytics: ConnectionCategory.ANALYTICS,
    "E-commerce": ConnectionCategory.ECOMMERCE,
    Communication: ConnectionCategory.COMMUNICATION,
    Custom: ConnectionCategory.CUSTOM,
  };

  return labelMap[label] || null;
};

/**
 * Get all available category labels for display in dropdowns
 */
export const getAllCategoryLabels = (): string[] => {
  return Object.values(ConnectionCategory).map(getCategoryLabel);
};
