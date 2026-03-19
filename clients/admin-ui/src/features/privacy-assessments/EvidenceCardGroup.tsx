import classNames from "classnames";
import { Space, Text } from "fidesui";

import { formatDate } from "~/features/common/utils";

import { FIELD_NAME_LABELS, SOURCE_TYPE_LABELS } from "./constants";
import styles from "./EvidenceCardGroup.module.scss";
import { SlackThreadCard } from "./SlackThreadCard";
import { EvidenceItem, EvidenceType } from "./types";

export interface EvidenceCardGroupProps {
  items: EvidenceItem[];
}

export const EvidenceCardGroup = ({ items }: EvidenceCardGroupProps) => (
  <Space direction="vertical" size="small" className={styles.itemList}>
    {items.map((item) =>
      item.type === EvidenceType.TEAM_INPUT ? (
        <SlackThreadCard key={item.id} item={item} />
      ) : (
        <div key={item.id} className={styles.evidenceCard}>
          <Text strong size="sm" className="mb-2 block">
            {SOURCE_TYPE_LABELS[item.source_type!] ?? item.source_type}
          </Text>
          <Text className={classNames("mb-2 block", styles.cardValue)}>
            <Text type="secondary">
              {FIELD_NAME_LABELS[item.field_name!] ??
                item.field_name!.replace(/_/g, " ")}
              :{" "}
            </Text>
            {item.value}
          </Text>
          <Text type="secondary" size="sm" className="block">
            {formatDate(item.created_at)}
          </Text>
        </div>
      ),
    )}
  </Space>
);
