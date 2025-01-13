import {
  AntButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MoreIcon,
} from "fidesui";

interface SystemActionsCellProps {
  onDetailClick?: () => void;
}

const SystemActionsCell = ({ onDetailClick }: SystemActionsCellProps) => {
  return (
    <Menu>
      <MenuButton
        as={AntButton}
        size="small"
        // Chakra is expecting the Chakra "type" prop, i.e. HTML type,
        // but Ant buttons use "type" for styling
        // @ts-ignore
        type="text"
        className="max-w-4"
        icon={<MoreIcon transform="rotate(90deg)" ml={2} />}
      />
      <MenuList>
        {onDetailClick && (
          <MenuItem onClick={onDetailClick}>View details</MenuItem>
        )}
      </MenuList>
    </Menu>
  );
};

export default SystemActionsCell;
