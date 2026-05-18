/**
 * Local types for the access package API responses.
 *
 * These mirror the fidesplus Pydantic schemas. Once the OpenAPI types are
 * generated from the fidesplus routes, these can be replaced with generated
 * imports + local overrides (to mark list fields as required).
 */

export enum RedactionType {
  REDACT = "redact",
  REMOVE_FIELD = "remove_field",
  REMOVE_RECORD = "remove_record",
}

export interface RedactionEntry {
  source: string;
  record_index: number;
  field_path: string | null;
  type: RedactionType;
}

export interface RedactionsRequest {
  redactions: RedactionEntry[];
}

export interface AccessPackageEntry {
  source: string;
  system?: string | null;
  system_name?: string | null;
  record_index: number;
  field_path: string;
  value?: unknown;
  redacted: boolean;
}

export interface AccessPackageCategory {
  fides_key: string;
  name: string;
  entries: AccessPackageEntry[];
}

export interface AccessPackageDataUse {
  fides_key: string;
  name: string;
  description: string;
  categories: AccessPackageCategory[];
}

export interface AccessPackageOther {
  name: string;
  description: string;
  categories: AccessPackageCategory[];
}

export interface AttachmentResponse {
  file_name: string;
  retrieved_attachment_size?: number | null;
}

export interface AccessPackageResponse {
  redactions: RedactionEntry[];
  data_uses: AccessPackageDataUse[];
  other?: AccessPackageOther | null;
  attachments: AttachmentResponse[];
}
