/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ExportFormat } from "./ExportFormat";

/**
 * Request schema for manual task export with field validation.
 *
 * Filter parameters (status, request_type, system_name, assigned_user_id, privacy_request_id)
 * are passed as QUERY PARAMETERS to match the search endpoint - users export what they see.
 *
 * Example:
 * POST /api/v1/manual-fields/export?status=new&request_type=access
 * Body: {"format": "csv", "fields": ["name", "status", "created_at"]}
 */
export type ManualTaskExportRequest = {
  /**
   * Export format
   */
  format?: ExportFormat;
  /**
   * List of field keys to include. Must be explicitly specified to ensure intentional data export, especially when PII is involved.
   */
  fields: Array<string>;
};
