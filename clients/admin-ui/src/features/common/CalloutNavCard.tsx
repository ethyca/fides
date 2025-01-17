import { AntCard as Card, AntTypography as Typography, Box } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

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
      <div className="mb-1 flex items-center gap-1.5">
        {icon}
        <Typography.Title
          level={5}
          style={{ marginBottom: 1, textAlign: "left" }}
        >
          {title}
        </Typography.Title>
      </div>
      <Typography.Text style={{ textAlign: "left" }}>
        {description}
      </Typography.Text>
    </Card>
  </Box>
);
export default CalloutNavCard;
