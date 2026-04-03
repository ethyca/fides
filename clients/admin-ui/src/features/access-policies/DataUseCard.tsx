import { antTheme, Card, Icons } from "fidesui";

import useTaxonomies from "../common/hooks/useTaxonomies";
import { DATA_USE_ICON } from "./constants";

const ICON_MAP: Record<string, Icons.CarbonIconType> = {
  Security: Icons.Locked,
  ChartBar: Icons.DataAnalytics,
  Analytics: Icons.DataAnalytics,
  Building: Icons.DataBase,
  Receipt: Icons.Document,
  UserProfile: Icons.UserAvatar,
  GroupPresentation: Icons.User,
  Chat: Icons.MessageQueue,
  Document: Icons.Document,
  Task: Icons.RuleDraft,
  Folder: Icons.Layers,
};

interface DataUseCardProps {
  dataUseId: string;
  isSelected: boolean;
  onClick: () => void;
}

const DataUseCard = ({ dataUseId, isSelected, onClick }: DataUseCardProps) => {
  const { token } = antTheme.useToken();
  const { getDataUseDisplayName } = useTaxonomies();

  const title = getDataUseDisplayName(dataUseId);
  const iconName = DATA_USE_ICON[dataUseId];
  const IconComponent = ICON_MAP[iconName] ?? Icons.DataAnalytics;

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
