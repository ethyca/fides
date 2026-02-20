import {
  Button,
  Drawer,
  DrawerProps,
  Flex,
  Icons,
  Input,
  Space,
  Text,
  Title,
  useMessage,
} from "fidesui";

import styles from "./EvidenceDrawer.module.scss";
import { EvidenceSection } from "./EvidenceSection";
import { EvidenceItem, QuestionGroup } from "./types";

interface EvidenceDrawerProps extends Omit<DrawerProps, "onClose"> {
  open: boolean;
  onClose: () => void;
  focusedGroupId: string | null;
  questionGroups: QuestionGroup[];
  evidence: EvidenceItem[];
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export const EvidenceDrawer = ({
  open,
  onClose,
  focusedGroupId,
  questionGroups,
  evidence,
  searchQuery,
  onSearchChange,
  ...props
}: EvidenceDrawerProps) => {
  const message = useMessage();

  return (
    <Drawer
      {...props}
      title={
        <Flex
          justify="space-between"
          align="center"
          className={styles.drawerTitle}
        >
          <div>
            <Title level={5} className={styles.drawerHeading}>
              Evidence
            </Title>
            <Text type="secondary" size="sm">
              Complete evidence trail organized by question
            </Text>
          </div>
          <Button
            type="text"
            icon={<Icons.Download size={16} />}
            size="small"
            onClick={() => message.success("Evidence report exported")}
          >
            Export
          </Button>
        </Flex>
      }
      placement="right"
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
        <Space direction="vertical" size="large" className={styles.content}>
          {focusedGroupId && (
            <EvidenceSection
              groupId={focusedGroupId}
              group={questionGroups.find((g) => g.id === focusedGroupId)}
              evidence={evidence}
            />
          )}
        </Space>
      </div>
    </Drawer>
  );
};
