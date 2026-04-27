// Local overrides for the access-package response shape.
// The generator marks list fields as optional because the backend Pydantic
// schemas use `default_factory=list`, but the API always returns arrays.
// Treat them as required here so the UI doesn't have to guard every access.

import type {
  AccessPackageCategory as GeneratedAccessPackageCategory,
  AccessPackageDataUse as GeneratedAccessPackageDataUse,
  AccessPackageEntry as GeneratedAccessPackageEntry,
  AccessPackageOther as GeneratedAccessPackageOther,
  AccessPackageResponse as GeneratedAccessPackageResponse,
  AttachmentResponse,
  RedactionEntry,
} from "~/types/api";

export type AccessPackageEntry = GeneratedAccessPackageEntry & {
  redacted: boolean;
};

export type AccessPackageCategory = Omit<
  GeneratedAccessPackageCategory,
  "entries"
> & {
  entries: AccessPackageEntry[];
};

export type AccessPackageDataUse = Omit<
  GeneratedAccessPackageDataUse,
  "categories"
> & {
  categories: AccessPackageCategory[];
};

export type AccessPackageOther = Omit<
  GeneratedAccessPackageOther,
  "name" | "description" | "categories"
> & {
  // The Pydantic schema defaults name and description to non-empty strings,
  // so they are always present at runtime even though the generator marks
  // them optional.
  name: string;
  description: string;
  categories: AccessPackageCategory[];
};

export type AccessPackageResponse = Omit<
  GeneratedAccessPackageResponse,
  "data_uses" | "redactions" | "other" | "attachments"
> & {
  data_uses: AccessPackageDataUse[];
  redactions: RedactionEntry[];
  other?: AccessPackageOther | null;
  attachments: AttachmentResponse[];
};
