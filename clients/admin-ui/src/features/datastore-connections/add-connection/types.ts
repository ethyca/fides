export type AddConnectionStep = {
  stepId: number;
  label: string;
  href: string;
  description?: string;
  parentStepId?: number;
};

export type SassConnectorTemplate = {
  description: string;
  instance_key: string;
  name: string;
  [key: string]: any;
};
