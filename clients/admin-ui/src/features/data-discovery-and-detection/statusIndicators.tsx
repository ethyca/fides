import { Icons } from "fidesui";

import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";

export const AdditionIndicator = () => (
  <Icons.ArrowUpRight
    style={{ color: "var(--ant-color-success)" }}
    className="size-2"
    data-testid="add-icon"
  />
);

export const RemovalIndicator = () => (
  <Icons.ArrowDownRight
    style={{ color: "var(--ant-color-error)" }}
    className="size-2"
    data-testid="remove-icon"
  />
);

export const ClassificationIndicator = () => (
  <Icons.Tag
    style={{ color: "var(--ant-color-warning)" }}
    className="size-3"
    data-testid="classify-icon"
  />
);

const CircleIndicator = ({ color, ...props }: { color: string }) => (
  <Icons.CircleSolid style={{ color }} className="size-2" {...props} />
);

export const ChangeIndicator = () => (
  <CircleIndicator color="var(--ant-color-info)" data-testid="change-icon" />
);

export const MonitoredIndicator = () => (
  <CircleIndicator
    color="var(--ant-color-success)"
    data-testid="monitored-icon"
  />
);

export const MutedIndicator = () => (
  <CircleIndicator color="var(--ant-color-error)" data-testid="muted-icon" />
);

export const InProgressIndicator = () => (
  <CircleIndicator
    color="var(--ant-color-warning)"
    data-testid="in-progress-icon"
  />
);

export const STATUS_INDICATOR_MAP: Record<
  ResourceChangeType,
  JSX.Element | null
> = {
  [ResourceChangeType.ADDITION]: <AdditionIndicator />,
  [ResourceChangeType.REMOVAL]: <RemovalIndicator />,
  [ResourceChangeType.CLASSIFICATION]: <ClassificationIndicator />,
  [ResourceChangeType.CHANGE]: <ChangeIndicator />,
  [ResourceChangeType.MONITORED]: <MonitoredIndicator />,
  [ResourceChangeType.MUTED]: <MutedIndicator />,
  [ResourceChangeType.IN_PROGRESS]: <InProgressIndicator />,
  [ResourceChangeType.NONE]: null,
};
