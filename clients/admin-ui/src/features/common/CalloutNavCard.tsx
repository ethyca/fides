import { AntCard as Card, AntTypography as Typography, Box } from "fidesui";

import styles from "./CalloutNavCard.module.scss";

interface CalloutNavCardProps {
  color: string;
  title: string;
  description: string;
  icon?: React.ReactElement;
}

const CalloutNavCard = ({
  color,
  description,
  title,
  icon,
}: CalloutNavCardProps) => (
  <Box
    borderLeft={`9px solid ${color}`}
    borderRadius="6px"
    className={styles.container}
  >
    <Card className={styles.card} data-testid={`tile-${title}`}>
      <div className="mb-1 flex items-center gap-1.5">
        {icon}
        <Typography.Title level={3}>{title}</Typography.Title>
      </div>
      <Typography.Text>{description}</Typography.Text>
    </Card>
  </Box>
);
export default CalloutNavCard;
