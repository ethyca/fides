/**
 * Access package types consumed by the admin UI.
 *
 * Where the generated OpenAPI types match the consumer's expectations, we
 * re-export them directly. Where the backend's Pydantic schemas mark list
 * fields as `Optional[list[...]] = None` (even though the response always
 * includes them in practice), we override locally so the UI can rely on
 * required values without `?? []` fallbacks scattered everywhere.
 */

import type {
  AccessPackageCategory as GeneratedAccessPackageCategory,
  AccessPackageDataUse as GeneratedAccessPackageDataUse,
  AccessPackageEntry as GeneratedAccessPackageEntry,
  AccessPackageOther as GeneratedAccessPackageOther,
  AttachmentResponse,
  RedactionEntry,
} from "~/types/api";

/**
 * Override: `redacted` is required. The backend always populates it.
 */
export interface AccessPackageEntry extends Omit<
  GeneratedAccessPackageEntry,
  "redacted"
> {
  redacted: boolean;
}

/**
 * Override: `entries` is required. The backend always returns the list,
 * possibly empty.
 */
export interface AccessPackageCategory extends Omit<
  GeneratedAccessPackageCategory,
  "entries"
> {
  entries: AccessPackageEntry[];
}

/**
 * Override: `description` and `categories` are required.
 */
export interface AccessPackageDataUse extends Omit<
  GeneratedAccessPackageDataUse,
  "description" | "categories"
> {
  description: string;
  categories: AccessPackageCategory[];
}

/**
 * Override: `name`, `description`, and `categories` are required.
 */
export interface AccessPackageOther extends Omit<
  GeneratedAccessPackageOther,
  "name" | "description" | "categories"
> {
  name: string;
  description: string;
  categories: AccessPackageCategory[];
}

/**
 * Override of the generated `AccessPackageResponse`:
 * - tightens `redactions`, `data_uses`, and `attachments` from optional to
 *   required
 * - replaces the generated `attachments: Array<unknown>` with the real
 *   `AttachmentResponse` shape from `~/types/api`
 * - uses the local (tightened) `AccessPackageDataUse` / `AccessPackageOther`
 *   so consumers don't have to guard against missing `categories`/`entries`
 */
export interface AccessPackageResponse {
  redactions: RedactionEntry[];
  data_uses: AccessPackageDataUse[];
  other?: AccessPackageOther | null;
  attachments: AttachmentResponse[];
}
