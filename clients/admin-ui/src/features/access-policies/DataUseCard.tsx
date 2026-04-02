import { antTheme, Card, Icons } from "fidesui";

import { DATA_USE_DISPLAY } from "./constants";

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
  dataUseId: string;
  isSelected: boolean;
  onClick: () => void;
}

const DataUseCard = ({ dataUseId, isSelected, onClick }: DataUseCardProps) => {
  const { token } = antTheme.useToken();
  const display = DATA_USE_DISPLAY[dataUseId];
  const title = display?.title ?? dataUseId;
  const IconComponent = ICON_MAP[display?.iconName] ?? Icons.DataAnalytics;

  return (
    <Card
      hoverable
      onClick={onClick}
      size="small"
      style={{
        cursor: "pointer",
        borderColor: isSelected ? token.colorSuccess : undefined,
        backgroundColor: isSelected ? token.colorSuccessBg : undefined,
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
            style={{ color: token.colorSuccess }}
          />
        )}
      </div>
    </Card>
  );
};

export default DataUseCard;
