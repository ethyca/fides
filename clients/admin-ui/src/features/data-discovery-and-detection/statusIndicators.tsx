import { Icons } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import { RightDownArrowIcon } from "~/features/common/Icon/svg/RightDownArrowIcon";
import { RightUpArrowIcon } from "~/features/common/Icon/svg/RightUpArrowIcon";
import { TagIcon } from "~/features/common/Icon/svg/TagIcon";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";

export const AdditionIndicator = () => (
  <RightUpArrowIcon
    style={{ color: palette.FIDESUI_SUCCESS }}
    className="size-2"
    data-testid="add-icon"
  />
);

export const RemovalIndicator = () => (
  <RightDownArrowIcon
    style={{ color: palette.FIDESUI_ERROR }}
    className="size-2"
    data-testid="remove-icon"
  />
);

export const ClassificationIndicator = () => (
  <TagIcon
    style={{ color: palette.FIDESUI_WARNING }}
    className="size-3"
    data-testid="classify-icon"
  />
);

const CircleIndicator = ({ color, ...props }: { color: string }) => (
  <Icons.CircleSolid style={{ color }} className="size-2" {...props} />
);

export const ChangeIndicator = () => (
  <CircleIndicator color={palette.FIDESUI_INFO} data-testid="change-icon" />
);

export const MonitoredIndicator = () => (
  <CircleIndicator
    color={palette.FIDESUI_SUCCESS}
    data-testid="monitored-icon"
  />
);

export const MutedIndicator = () => (
  <CircleIndicator color={palette.FIDESUI_ERROR} data-testid="muted-icon" />
);

export const InProgressIndicator = () => (
  <CircleIndicator
    color={palette.FIDESUI_WARNING}
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
