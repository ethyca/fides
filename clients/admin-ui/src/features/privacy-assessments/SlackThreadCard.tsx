import { format } from "date-fns-tz";
import { Avatar, Collapse, List, Text } from "fidesui";

import Image from "~/features/common/Image";
import { formatDate, pluralize } from "~/features/common/utils";

import styles from "./SlackThreadCard.module.scss";
import { EvidenceItem, SlackMessage } from "./types";
import { getInitials } from "./utils";

interface SlackThreadCardProps {
  item: EvidenceItem;
}

export const SlackThreadCard = ({ item }: SlackThreadCardProps) => {
  const { data } = item;
  if (!data) {
    return null;
  }
  return (
    <div className={styles.slackCard}>
      <Text strong size="sm" className="mb-2 block">
        Stakeholder communication
      </Text>

      <Text size="sm" className="mb-2 block">
        {item.value}
      </Text>

      <Text type="secondary" size="sm" className="block">
        {data.channel || "N/A"} &middot; {data.messages.length}{" "}
        {pluralize(data.messages.length, "message", "messages")} &middot;{" "}
        {formatDate(item.created_at)}
      </Text>

      {data.messages.length > 0 && (
        <Collapse
          ghost
          className="mt-2"
          items={[
            {
              key: "thread",
              label: `View ${data.messages.length} ${pluralize(data.messages.length, "message", "messages")}`,
              children: (
                <List
                  size="small"
                  dataSource={data.messages}
                  renderItem={(msg: SlackMessage) => (
                    <List.Item className={styles.messageItem}>
                      <List.Item.Meta
                        avatar={
                          msg.is_bot ? (
                            <Avatar
                              shape="square"
                              className={styles.messageAvatarBot}
                              icon={
                                <Image
                                  src="/images/logomark-astralis-white.svg"
                                  alt="Fides"
                                  width={12}
                                  height={12}
                                  className={styles.messageAvatarImage}
                                />
                              }
                            />
                          ) : (
                            <Avatar
                              shape="square"
                              className={styles.messageAvatarUser}
                            >
                              {getInitials(msg.sender)}
                            </Avatar>
                          )
                        }
                        title={
                          <Text strong size="sm">
                            {msg.sender}
                            {msg.timestamp && (
                              <Text type="secondary" size="sm" className="ml-2">
                                {format(
                                  new Date(msg.timestamp),
                                  "MMM d, hh:mm aa",
                                )}
                              </Text>
                            )}
                          </Text>
                        }
                        description={
                          <Text size="sm" className="mt-1 block">
                            {msg.text}
                          </Text>
                        }
                      />
                    </List.Item>
                  )}
                />
              ),
            },
          ]}
        />
      )}
    </div>
  );
};
