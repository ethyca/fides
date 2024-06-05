import { Box, EditIcon, IconButton } from "fidesui";

const MonitorConfigActionsCell = ({
  onEditClick,
}: {
  onEditClick: () => void;
}) => (
  <Box>
    <IconButton
      onClick={onEditClick}
      icon={<EditIcon />}
      variant="outline"
      size="xs"
      data-testid="edit-monitor-btn"
      aria-label="Edit monitor"
    />
  </Box>
);

export default MonitorConfigActionsCell;
