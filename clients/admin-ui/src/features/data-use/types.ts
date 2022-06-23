import { FidesKey } from "../common/fides-types";

export interface DataUse {
  fides_key: string;
  organization_fides_key: "default_organization";
  name: string;
  description: string;
  parent_key: FidesKey | null;
  legal_basis: "Consent";
  special_category: "Consent";
  recipients: string[];
  legitimate_interest: false;
  legitimate_interest_impact_assessment: string;
}
