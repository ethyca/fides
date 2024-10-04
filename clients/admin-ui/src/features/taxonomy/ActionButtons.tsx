import {
  AntButton,
  AntSwitch as Switch,
  DeleteIcon,
  EditIcon,
  HStack,
  Text,
} from "fidesui";

import { TaxonomyEntityNode } from "./types";

interface ActionButtonProps {
  node: TaxonomyEntityNode;
  onEdit: (node: TaxonomyEntityNode) => void;
  onDelete: (node: TaxonomyEntityNode) => void;
  onDisable: (node: TaxonomyEntityNode) => void;
}
const ActionButtons = ({
  node,
  onEdit,
  onDelete,
  onDisable,
}: ActionButtonProps) => {
  const showDelete = !node.is_default;
  return (
    <HStack mr={4}>
      <div data-testid="action-btns">
        <AntButton
          aria-label="Edit"
          size="small"
          icon={<EditIcon boxSize={3} />}
          onClick={() => onEdit(node)}
          data-testid="edit-btn"
        />
        {showDelete && (
          <AntButton
            aria-label="Delete"
            size="small"
            icon={<DeleteIcon boxSize={3} />}
            onClick={() => onDelete(node)}
            data-testid="delete-btn"
          />
        )}
      </div>
      <Switch
        size="small"
        defaultChecked={node.active}
        onChange={() => onDisable(node)}
      />
      <Text>Enabled</Text>
    </HStack>
  );
};

export default ActionButtons;
