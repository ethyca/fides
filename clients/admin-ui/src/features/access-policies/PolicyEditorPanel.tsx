import { Button, Flex, Icons, Popconfirm, Space } from "fidesui";
import React from "react";

import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

interface PolicyEditorPanelProps {
  title: string;
  breadcrumbTitle: string;
  isNew: boolean;
  onDelete?: () => void;
  onExport: () => void;
  onSave: () => void;
  children: React.ReactNode;
}

const PolicyEditorPanel = ({
  title,
  breadcrumbTitle,
  isNew,
  onDelete,
  onExport,
  onSave,
  children,
}: PolicyEditorPanelProps) => (
  <div className="h-full overflow-hidden pb-4 pl-10 pr-3 pt-6">
    <Flex vertical className="h-full min-w-0 grow">
      <div>
        <PageHeader
          heading={title}
          breadcrumbItems={[
            { title: "Access policies", href: ACCESS_POLICIES_ROUTE },
            { title: breadcrumbTitle },
          ]}
          rightContent={
            <Space>
              {!isNew && (
                <Popconfirm
                  title="Delete policy"
                  description="Are you sure you want to delete this policy?"
                  onConfirm={onDelete}
                  okText="Delete"
                  okButtonProps={{ danger: true }}
                  cancelText="Cancel"
                >
                  <Button
                    icon={<Icons.TrashCan />}
                    danger
                    aria-label="Delete policy"
                    data-testid="delete-btn"
                  />
                </Popconfirm>
              )}
              <Button
                icon={<Icons.Download />}
                onClick={onExport}
                data-testid="export-btn"
              >
                Export
              </Button>
              <Button type="primary" onClick={onSave} data-testid="save-btn">
                Save
              </Button>
            </Space>
          }
        />
      </div>
      <div className="relative min-h-0 grow">{children}</div>
    </Flex>
  </div>
);

export default PolicyEditorPanel;
