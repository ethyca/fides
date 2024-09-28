import {
  AntSwitch as Switch,
  ButtonGroup,
  DeleteIcon,
  EditIcon,
  HStack,
  IconButton,
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
      <ButtonGroup
        size="xs"
        variant="outline"
        colorScheme="gray"
        data-testid="action-btns"
      >
        <IconButton
          aria-label="Edit"
          icon={<EditIcon boxSize={3} />}
          onClick={() => onEdit(node)}
          data-testid="edit-btn"
        />
        {showDelete ? (
          <IconButton
            aria-label="Delete"
            icon={<DeleteIcon boxSize={3} />}
            onClick={() => onDelete(node)}
            data-testid="delete-btn"
          />
        ) : null}
      </ButtonGroup>
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
