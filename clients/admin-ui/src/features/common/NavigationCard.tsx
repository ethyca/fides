import { AntCard, AntTypography, Box } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

interface NavigationCardProps {
  color: string;
  title: string;
  description: string;
}

const NavigationCard = ({ color, description, title }: NavigationCardProps) => (
  <Box
    borderLeft={`9px solid ${color}`}
    borderRadius="6px"
    className="flex grow"
  >
    <AntCard
      className="grow"
      style={{
        backgroundColor: palette.FIDESUI_CORINTH,
        borderRadius: "0px 6px 6px 0px",
        borderLeft: "none",
      }}
      data-testid={`tile-${title}`}
    >
      <AntTypography.Title level={5}>{title}</AntTypography.Title>
      <AntTypography.Text>{description}</AntTypography.Text>
    </AntCard>
  </Box>
);
export default NavigationCard;
