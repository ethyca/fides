export interface DataSubject {
  fides_key: string;
  organization_fides_key: "default_organization";
  name: string;
  description: string;
  rights: {
    strategy: "ALL";
    values: ["Informed"];
  };
  automated_decisions_or_profiling: true;
}
