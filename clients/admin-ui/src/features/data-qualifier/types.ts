import { FidesKey } from "../common/fides-types";

export interface DataQualifier {
  fides_key: string;
  organization_fides_key: "default_organization";
  name: string;
  description: string;
  parent_key: FidesKey | null;
}
