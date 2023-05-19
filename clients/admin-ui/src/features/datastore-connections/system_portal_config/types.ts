import { SystemType } from "~/types/api";

export type AddConnectionStep = {
  stepId: number;
  label: string;
  href: string;
  description?: string;
  parentStepId?: number;
};

export type BaseConnectorParametersFields = {
  description: string;
  name: string;
  instance_key?: string;
  [key: string]: any;
};

export type ConnectorParameterOption = {
  type: SystemType;
  options: string[];
};

export type DatabaseConnectorParametersFormFields =
  BaseConnectorParametersFields;

export type SaasConnectorParametersFormFields = BaseConnectorParametersFields;
export type EmailConnectorParametersFormFields = BaseConnectorParametersFields;
