import { Card, Icons } from "fidesui";

const ICON_MAP: Record<string, Icons.CarbonIconType> = {
  Security: Icons.Security,
  ChartBar: Icons.ChartBar,
  Analytics: Icons.Analytics,
  Building: Icons.Building,
  Health: Icons.HealthCross,
  Search: Icons.Search,
  Receipt: Icons.Receipt,
  UserProfile: Icons.UserProfile,
  GroupPresentation: Icons.GroupPresentation,
  Chat: Icons.Chat,
  Document: Icons.Document,
  Task: Icons.Task,
  Warning: Icons.WarningAlt,
  Folder: Icons.Folder,
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
  const IconComponent = ICON_MAP[iconName] ?? Icons.Category;

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
