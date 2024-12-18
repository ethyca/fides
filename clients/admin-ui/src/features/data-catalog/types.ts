export enum DatasetLifecycleStatusEnum {
  ADDED = "Added",
  IN_PROGRESS = "In progress",
  ATTENTION = "Attention required",
}

export interface DatasetLifecycleStatusResult {
  status: DatasetLifecycleStatusEnum;
  detail: string;
}
