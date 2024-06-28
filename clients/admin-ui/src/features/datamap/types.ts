export type Link = {
  source: string;
  target: string;
};

export type SpatialData = {
  links: Link[];
  nodes: SystemNode[];
};

export type SystemNode = {
  ingress: string[];
  egress: string[];
  description: string;
  id: string;
  name: string;
};

export type SetSelectedSystemId = {
  setSelectedSystemId: (id: string) => void;
};
