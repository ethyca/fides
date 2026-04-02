export enum DataConsumerType {
  SERVICE = "service",
  APPLICATION = "application",
  GROUP = "group",
  USER = "user",
}

export const CONSUMER_TYPE_LABELS: Record<DataConsumerType, string> = {
  [DataConsumerType.SERVICE]: "Service",
  [DataConsumerType.APPLICATION]: "Application",
  [DataConsumerType.GROUP]: "Group",
  [DataConsumerType.USER]: "User",
};

export const CONSUMER_TYPE_OPTIONS = Object.entries(CONSUMER_TYPE_LABELS).map(
  ([value, label]) => ({ value, label }),
);

export const DATA_CONSUMER_FORM_ID = "data-consumer-form";
