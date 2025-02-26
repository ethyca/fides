import { CircleIcon } from "~/features/common/Icon/CircleIcon";
import { RightDownArrowIcon } from "~/features/common/Icon/RightDownArrowIcon";
import { RightUpArrowIcon } from "~/features/common/Icon/RightUpArrowIcon";
import { TagIcon } from "~/features/common/Icon/TagIcon";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";

export const AdditionIndicator = () => (
  <RightUpArrowIcon
    color="green.400"
    boxSize={2}
    mr={2}
    data-testid="add-icon"
  />
);

export const RemovalIndicator = () => (
  <RightDownArrowIcon
    color="red.400"
    boxSize={2}
    mr={2}
    data-testid="remove-icon"
  />
);

export const ClassificationIndicator = () => (
  <TagIcon color="orange.400" boxSize={3} mr={1} data-testid="classify-icon" />
);

export const ChangeIndicator = () => (
  <CircleIcon color="blue.400" boxSize={2} mr={2} data-testid="change-icon" />
);

export const MonitoredIndicator = () => (
  <CircleIcon
    color="green.400"
    boxSize={2}
    mr={2}
    data-testid="monitored-icon"
  />
);

export const MutedIndicator = () => (
  <CircleIcon color="red.400" boxSize={2} mr={2} data-testid="muted-icon" />
);

export const InProgressIndicator = () => (
  <CircleIcon
    color="orange.400"
    boxSize={2}
    mr={2}
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
