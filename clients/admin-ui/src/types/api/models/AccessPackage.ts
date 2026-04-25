// Hand-written until regenerated from fidesplus OpenAPI.
// Mirrors fidesplus/src/fidesplus/api/schemas/access_package.py

export enum RedactionType {
  REDACT = "redact",
  REMOVE_FIELD = "remove_field",
  REMOVE_RECORD = "remove_record",
}

export interface RedactionEntry {
  source: string;
  record_index: number;
  field_path?: string | null;
  type: RedactionType;
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

export interface AccessPackageResponse {
  redactions: RedactionEntry[];
  data_uses: AccessPackageDataUse[];
  other?: AccessPackageOther | null;
  attachments: unknown[];
}

export interface RedactionsRequest {
  redactions: RedactionEntry[];
}
