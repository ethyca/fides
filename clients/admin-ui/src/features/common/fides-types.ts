/**
 * Common Fides types adapted from https://github.com/ethyca/fideslang/blob/main/src/fideslang/models.py
 */

export type FidesKey = string;

export interface FidesBase {
  fides_key: FidesKey;
  organization_fides_key: FidesKey;
  tags?: string[];
  name?: string;
  description?: string;
}

export interface ContactDetails {
  name: string;
  address: string;
  email: string;
  phone: string;
}
