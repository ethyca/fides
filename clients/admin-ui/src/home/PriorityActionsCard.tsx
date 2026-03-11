import classNames from "classnames";
import { Card, Empty, Flex, Skeleton, Tag, Typography } from "fidesui";
import { useMemo, useState } from "react";

import { useGetPriorityActionsQuery } from "~/features/dashboard/dashboard.slice";

import cardStyles from "./dashboard-card.module.scss";
import styles from "./PriorityActionsCard.module.scss";

export const PriorityActionsCard = () => {
  const { data: actions, isLoading: loading } = useGetPriorityActionsQuery();
  const [activeTab, setActiveTab] = useState("act_now");

  const filteredActions = useMemo(() => {
    if (!actions?.items) {
      return [];
    }
    if (activeTab === "act_now") {
      return actions.items.filter((a) => a.due_date !== null);
    }
    return actions.items.filter((a) => a.due_date === null);
  }, [actions, activeTab]);

  const actNowCount = useMemo(
    () => actions?.items?.filter((a) => a.due_date !== null).length ?? 0,
    [actions],
  );
  const dueLaterCount = useMemo(
    () => actions?.items?.filter((a) => a.due_date === null).length ?? 0,
    [actions],
  );

  return (
    <Card
      title="Priority actions"
      variant="borderless"
      className={classNames("h-full", cardStyles.dashboardCard)}
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
      {(() => {
        if (loading) {
          return <Skeleton active />;
        }
        if (filteredActions.length === 0) {
          return (
            <Flex
              align="center"
              justify="center"
              className={styles.emptyActions}
            >
              <Empty
                description={`No ${activeTab === "act_now" ? "urgent" : "upcoming"} actions`}
              />
            </Flex>
          );
        }
        return (
          <Flex vertical gap={8} className="pt-3">
            {filteredActions.map((action) => (
              <Card
                key={action.id}
                variant="borderless"
                hoverable
                className="cursor-pointer"
              >
                <Flex justify="space-between" align="start">
                  <div>
                    <Typography.Text strong>{action.title}</Typography.Text>
                    <br />
                    <Typography.Text type="secondary">
                      {action.message}
                    </Typography.Text>
                  </div>
                  <Flex gap={8} align="center">
                    {action.due_date && (
                      <Typography.Text type="secondary" className="text-sm">
                        {new Date(action.due_date).toLocaleDateString()}
                      </Typography.Text>
                    )}
                    <Tag>{action.action.replace(/_/g, " ")}</Tag>
                  </Flex>
                </Flex>
              </Card>
            ))}
          </Flex>
        );
      })()}
    </Card>
  );
};
