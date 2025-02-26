import { SystemType } from "~/types/api";

export type AddConnectionStep = {
  stepId: number;
  label: string;
  href: string;
  description?: string;
  parentStepId?: number;
};

export type ConnectionConfigFormValues = {
  description?: string;
  name?: string;
  instance_key?: string;
  enabled_actions?: string[];
  dataset?: string[];
  [key: string]: any;
};

export type ConnectorParameterOption = {
  type: SystemType;
  options: string[];
};
