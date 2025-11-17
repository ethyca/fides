/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { IdentityDefinitionType } from "./IdentityDefinitionType";
import type { IndexStatus } from "./IndexStatus";

/**
 * Domain entity for identity definitions.
 *
 * Pydantic model, decoupled from SQLAlchemy ORM.
 * Session-independent and can be freely passed around, serialized, and cached.
 * Provides automatic validation and JSON serialization.
 */
export type IdentityDefinitionEntity = {
  identity_key: string;
  name: string;
  description?: string | null;
  type: IdentityDefinitionType;
  created_at: string;
  updated_at: string;
  created_by?: string | null;
  index_status?: IndexStatus | null;
};
