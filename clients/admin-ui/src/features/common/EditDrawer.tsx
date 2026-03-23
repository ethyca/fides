import { Button, Drawer, Flex, Icons } from "fidesui";
import type { ReactNode } from "react";


interface Props {
  title?: ReactNode;
  /** @deprecated Use `title` prop instead */
  header?: ReactNode;
  description?: string;
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}

/**
 * @deprecated Use `title` prop directly instead of wrapping in EditDrawerHeader.
 */
export const EditDrawerHeader = ({ title }: { title: string }): ReactNode =>
  title;

export const EditDrawerFooter = ({
  onDelete,
  onEditYaml,
  formId,
  isSaving,
}: {
  /**
   * Associates the submit button with a form, which is useful for when the button
   * does not live directly inside the form hierarchy
   */
  formId?: string;
  isSaving?: boolean;
  onDelete?: () => void;
  onEditYaml?: () => void;
}) => (
  <Flex justify="space-between" align="center">
    {onDelete ? (
      <Button
        aria-label="delete"
        icon={<Icons.TrashCan />}
        onClick={onDelete}
        data-testid="delete-btn"
      />
    ) : (
      <span />
    )}
    <div className="flex gap-2">
      {onEditYaml && (
        <Button onClick={onEditYaml} data-testid="edit-yaml-btn">
          Edit YAML
        </Button>
      )}
      <Button
        htmlType="submit"
        type="primary"
        data-testid="save-btn"
        form={formId}
        loading={isSaving}
      >
        Save
      </Button>
    </div>
  </Flex>
);

const EditDrawer = ({
  title,
  header,
  description,
  isOpen,
  onClose,
  children,
  footer,
}: Props) => (
  <Drawer
    open={isOpen}
    onClose={onClose}
    title={title ?? header}
    footer={footer}
    maskClosable={false}
    destroyOnHidden
  >
    <section data-testid="edit-drawer-content">
      {description ? (
        <p className="mb-4 text-sm text-gray-600">{description}</p>
      ) : null}
      {children}
    </section>
  </Drawer>
);

export default EditDrawer;
