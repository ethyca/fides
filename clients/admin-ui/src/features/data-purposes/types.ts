export interface DataPurpose {
  id: string;
  name: string;
  key: string;
  description: string;
  data_use: string;
  /** Categories declared as in-scope for this purpose (human-authored policy). */
  data_categories: string[];
  /** Categories the classifier has found on datasets/fields declaring this purpose. */
  detected_data_categories: string[];
  data_subjects: string[];
  legal_basis: string;
  legal_basis_is_flexible: boolean;
  retention_period_days: number | null;
  special_category_legal_basis: string | null;
  features: string[];
  sub_types: string[];
  updated_at: string;
}

export type ComplianceStatus = "compliant" | "drift" | "unknown";

export interface CategoryDrift {
  status: ComplianceStatus;
  /** Detected categories not in the defined set (scope drift). */
  undeclared: string[];
  /** Defined categories not in the detected set (unused declarations). */
  unused: string[];
}

export interface PurposeSystemAssignment {
  system_id: string;
  system_name: string;
  system_type: string;
  assigned: boolean;
  /** Whether this consumer is a system/integration or a user group. */
  consumer_category?: "system" | "group";
}

export interface PurposeCoverage {
  systems: { assigned: number; total: number };
  datasets: { assigned: number; total: number };
  tables: { assigned: number; total: number };
  fields: { assigned: number; total: number };
}

export interface PurposeDatasetAssignment {
  dataset_fides_key: string;
  dataset_name: string;
  system_name: string;
  collection_count: number;
  /** Categories the classifier detected on this specific dataset. */
  data_categories: string[];
  /** When the dataset's metadata / classification was last updated. */
  updated_at: string;
  /** Person accountable for the dataset's governance. */
  steward: string;
}

export interface AvailableSystem {
  system_id: string;
  system_name: string;
  system_type: string;
}

export interface AvailableDataset {
  dataset_fides_key: string;
  dataset_name: string;
  system_name: string;
}

export interface PurposeSummary {
  id: string;
  name: string;
  system_count: number;
  dataset_count: number;
  badge_count: number;
}
