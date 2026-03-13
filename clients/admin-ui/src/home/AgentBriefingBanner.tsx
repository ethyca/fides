import { Alert, Button } from "fidesui";

import styles from "./AgentBriefingBanner.module.scss";

interface AgentBriefingBannerProps {
  briefing: string;
  onClose: () => void;
  onViewActions: () => void;
}

const AgentBriefingBanner = ({
  briefing,
  onClose,
  onViewActions,
}: AgentBriefingBannerProps) => (
  <Alert
    type="info"
    showIcon
    closable
    onClose={onClose}
    message={briefing}
    action={
      <Button size="small" type="link" onClick={onViewActions}>
        View actions
      </Button>
    }
    className={styles.alertSm}
  />
);

export default AgentBriefingBanner;
