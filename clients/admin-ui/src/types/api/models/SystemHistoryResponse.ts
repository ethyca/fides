import { SystemHistory } from "./SystemHistory";

export type SystemHistoryResponse = {
  items: SystemHistory[];
  total: number;
  page: number;
  size: number;
};
