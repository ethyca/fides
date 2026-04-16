import { Button, List, Text, Typography, useMessage, useModal } from "fidesui";
import type { NextPage } from "next";

import {
  Control,
  useDeleteControlMutation,
  useGetControlsQuery,
} from "~/features/access-policies/access-policies.slice";
import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { RouterLink } from "~/features/common/nav/RouterLink";
import {
  ACCESS_POLICIES_ROUTE,
  CONTROLS_EDIT_ROUTE,
  CONTROLS_NEW_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { RTKErrorResult } from "~/types/errors/api";

const ControlsPage: NextPage = () => {
  const message = useMessage();
  const modal = useModal();
  const { data: controls = [], isLoading } = useGetControlsQuery();
  const [deleteControl] = useDeleteControlMutation();

  const handleDelete = (control: Control) => {
    modal.confirm({
      title: "Delete control",
      content: (
        <span className="text-gray-500">
          Are you sure you want to delete the control &quot;{control.label}
          &quot;? This action cannot be undone.
        </span>
      ),
      okText: "Delete",
      okButtonProps: { danger: true },
      centered: true,
      onOk: async () => {
        try {
          await deleteControl(control.key).unwrap();
          message.success(`Control "${control.label}" deleted successfully`);
        } catch (error) {
          message.error(getErrorMessage(error as RTKErrorResult["error"]));
        }
      },
    });
  };

  return (
    <Layout title="Controls">
      <PageHeader
        heading="Controls"
        breadcrumbItems={[
          { title: "Access policies", href: ACCESS_POLICIES_ROUTE },
          { title: "Controls" },
        ]}
        rightContent={
          <RouterLink href={CONTROLS_NEW_ROUTE}>
            <Button type="primary">New control</Button>
          </RouterLink>
        }
      >
        <div className="max-w-3xl">
          <Text type="secondary">
            Controls are regulatory frameworks or compliance groupings used to
            organize access policies for reporting and management.
          </Text>
        </div>
      </PageHeader>
      <List
        loading={isLoading}
        itemLayout="horizontal"
        dataSource={controls}
        locale={{
          emptyText: (
            <div className="px-4 py-8 text-center">
              <Typography.Paragraph type="secondary">
                No controls yet. <br />
                Click &quot;New control&quot; to get started.
              </Typography.Paragraph>
            </div>
          ),
        }}
        renderItem={(control) => (
          <List.Item
            key={control.key}
            actions={[
              <Button
                key="delete"
                type="link"
                onClick={() => handleDelete(control)}
                data-testid="delete-list-btn"
                className="px-1"
              >
                Delete
              </Button>,
              <RouterLink
                key="edit"
                href={{
                  pathname: CONTROLS_EDIT_ROUTE,
                  query: { controlKey: control.key },
                }}
              >
                <Button
                  type="link"
                  data-testid="edit-list-btn"
                  className="px-1"
                >
                  Edit
                </Button>
              </RouterLink>,
            ]}
          >
            <List.Item.Meta
              title={control.label}
              description={control.description}
            />
          </List.Item>
        )}
      />
    </Layout>
  );
};

export default ControlsPage;
