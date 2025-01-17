import { AntCard as Card, AntTypography as Typography, Box } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

interface CalloutNavCardProps {
  color: string;
  title: string;
  description: string;
}

const CalloutNavCard = ({ color, description, title }: CalloutNavCardProps) => (
  <Box
    borderLeft={`9px solid ${color}`}
    borderRadius="6px"
    className="flex grow"
  >
    <Card
      className="grow"
      style={{
        backgroundColor: palette.FIDESUI_CORINTH,
        borderRadius: "0px 6px 6px 0px",
        borderLeft: "none",
      }}
      data-testid={`tile-${title}`}
    >
      <Typography.Title level={5}>{title}</Typography.Title>
      <Typography.Text>{description}</Typography.Text>
    </Card>
  </Box>
);
export default CalloutNavCard;
