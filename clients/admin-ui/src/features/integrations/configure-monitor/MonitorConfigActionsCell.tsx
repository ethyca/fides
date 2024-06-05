import { EditIcon, HStack, IconButton } from "fidesui";

const MonitorConfigActionsCell = ({
  onEditClick,
}: {
  onEditClick: () => void;
}) => (
  <HStack onClick={(e) => e.stopPropagation()} cursor="auto">
    <IconButton
      onClick={onEditClick}
      icon={<EditIcon />}
      variant="outline"
      size="xs"
      data-testid="edit-monitor-btn"
      aria-label="Edit monitor"
    />
  </HStack>
);

export default MonitorConfigActionsCell;
