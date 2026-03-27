import { Card, Icons } from "fidesui";

const ICON_MAP: Record<string, Icons.CarbonIconType> = {
  Security: Icons.Locked,
  ChartBar: Icons.DataAnalytics,
  Analytics: Icons.DataAnalytics,
  Building: Icons.DataBase,
  Health: Icons.Chemistry,
  Search: Icons.Search,
  Receipt: Icons.Document,
  UserProfile: Icons.UserAvatar,
  GroupPresentation: Icons.User,
  Chat: Icons.MessageQueue,
  Document: Icons.Document,
  Task: Icons.RuleDraft,
  Warning: Icons.WarningAlt,
  Folder: Icons.Layers,
};

interface DataUseCardProps {
  title: string;
  iconName: string;
  isSelected: boolean;
  onClick: () => void;
}

const DataUseCard = ({
  title,
  iconName,
  isSelected,
  onClick,
}: DataUseCardProps) => {
  const IconComponent = ICON_MAP[iconName] ?? Icons.DataAnalytics;

  return (
    <Card
      hoverable
      onClick={onClick}
      size="small"
      style={{
        cursor: "pointer",
        borderColor: isSelected ? "var(--fidesui-success)" : undefined,
        backgroundColor: isSelected ? "var(--fidesui-success-bg)" : undefined,
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <IconComponent size={16} />
          <span className="text-sm">{title}</span>
        </div>
        {isSelected && (
          <Icons.CheckmarkFilled
            size={16}
            style={{ color: "var(--fidesui-success)" }}
          />
        )}
      </div>
    </Card>
  );
};

export default DataUseCard;
