import { Drawer, DrawerProps, Icons, Input, Space, Text, Title } from "fidesui";

import styles from "./EvidenceDrawer.module.scss";
import { EvidenceSection } from "./EvidenceSection";
import { EvidenceItem, QuestionGroup } from "./types";

interface EvidenceDrawerProps extends Omit<DrawerProps, "onClose"> {
  open: boolean;
  onClose: () => void;
  focusedGroupId: string | null;
  group: QuestionGroup | undefined;
  evidence: EvidenceItem[];
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export const EvidenceDrawer = ({
  open,
  onClose,
  focusedGroupId,
  group,
  evidence,
  searchQuery,
  onSearchChange,
  ...props
}: EvidenceDrawerProps) => {
  return (
    <Drawer
      {...props}
      title={
        <div className={styles.drawerTitle}>
          <Title level={5} className={styles.drawerHeading}>
            Evidence
          </Title>
          <Text type="secondary" size="sm">
            Complete evidence trail organized by question
          </Text>
        </div>
      }
      onClose={onClose}
      open={open}
      width={600}
      className={styles.drawer}
    >
      <div className={styles.searchBar}>
        <Input
          placeholder="Search evidence..."
          prefix={<Icons.Search size={16} />}
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          allowClear
        />
      </div>
      <div className={styles.body}>
        <Space orientation="vertical" size="large" className={styles.content}>
          {focusedGroupId && (
            <EvidenceSection
              groupId={focusedGroupId}
              group={group}
              evidence={evidence}
              searchQuery={searchQuery}
            />
          )}
        </Space>
      </div>
    </Drawer>
  );
};
