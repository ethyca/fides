import { Button, ButtonGroup } from "@fidesui/react";

import { TaxonomyEntityNode } from "./types";

interface ActionButtonProps {
  node: TaxonomyEntityNode;
  onEdit: (node: TaxonomyEntityNode) => void;
  onDelete: (node: TaxonomyEntityNode) => void;
}
const ActionButtons = ({ node, onEdit, onDelete }: ActionButtonProps) => {
  const showDelete = node.children.length === 0 && !node.is_default;
  return (
    <ButtonGroup
      size="xs"
      isAttached
      variant="outline"
      data-testid="action-btns"
      mr="2"
    >
      <Button data-testid="edit-btn" onClick={() => onEdit(node)}>
        Edit
      </Button>
      {showDelete ? (
        <Button data-testid="delete-btn" onClick={() => onDelete(node)}>
          Delete
        </Button>
      ) : null}
    </ButtonGroup>
  );
};

export default ActionButtons;
