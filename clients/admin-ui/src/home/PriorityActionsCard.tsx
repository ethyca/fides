import { Button, Card, Empty, Flex, List, Tag, Text } from "fidesui";
import { useMemo, useState } from "react";

import { useGetPriorityActionsQuery } from "~/features/dashboard/dashboard.slice";

import { MOCK_PRIORITY_ACTIONS } from "./__mocks__/priorityActionsMock";
import styles from "./PriorityActionsCard.module.scss";

const USE_MOCK = true;

export const PriorityActionsCard = () => {
  const { data: apiActions, isLoading: apiLoading } =
    useGetPriorityActionsQuery();
  const [activeTab, setActiveTab] = useState("act_now");

  const actions = useMemo(
    () =>
      USE_MOCK
        ? { items: MOCK_PRIORITY_ACTIONS, total: MOCK_PRIORITY_ACTIONS.length }
        : apiActions,
    [apiActions],
  );
  const loading = USE_MOCK ? false : apiLoading;

  const filteredActions = useMemo(() => {
    if (!actions?.items) {
      return [];
    }
    if (activeTab === "act_now") {
      return actions.items.filter((a) => a.due_date !== null);
    }
    return actions.items.filter((a) => a.due_date === null);
  }, [actions, activeTab]);

  const actNowCount = actions?.items?.filter((a) => a.due_date !== null).length ?? 0;
  const dueLaterCount = actions?.items?.filter((a) => a.due_date === null).length ?? 0;

  return (
    <Card
      title="Priority actions"
      variant="borderless"
      className={styles.cardContainer}
      headerLayout="inline"
      tabList={[
        {
          key: "act_now",
          label: (
            <span>
              Act now <Tag color="default">{actNowCount}</Tag>
            </span>
          ),
        },
        {
          key: "due_later",
          label: (
            <span>
              Due later <Tag color="default">{dueLaterCount}</Tag>
            </span>
          ),
        },
      ]}
      activeTabKey={activeTab}
      onTabChange={setActiveTab}
    >
      <List
        dataSource={filteredActions}
        loading={loading}
        locale={{
          emptyText: (
            <Flex
              align="center"
              justify="center"
              className={styles.emptyActions}
            >
              <Empty
                description={`No ${activeTab === "act_now" ? "urgent" : "upcoming"} actions`}
              />
            </Flex>
          ),
        }}
        size="small"
        renderItem={(action) => (
          <List.Item
            key={action.id}
            actions={[
              <Button key="resolve" size="small" onClick={() => {}}>
                Resolve issue
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={
                <Text strong className="text-xs">
                  {action.title}
                </Text>
              }
              description={
                <Text type="secondary" className="text-xs">
                  {action.message}
                </Text>
              }
            />
          </List.Item>
        )}
      />
    </Card>
  );
};
