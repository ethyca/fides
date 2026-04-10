import { antTheme, Card, Icons } from "fidesui";

import useTaxonomies from "../common/hooks/useTaxonomies";

interface DataUseCardProps {
  dataUseId: string;
  isSelected: boolean;
  onClick: () => void;
}

const DataUseCard = ({ dataUseId, isSelected, onClick }: DataUseCardProps) => {
  const { token } = antTheme.useToken();
  const { getDataUseDisplayName } = useTaxonomies();

  const title = getDataUseDisplayName(dataUseId);

  return (
    <Card
      hoverable
      onClick={onClick}
      size="small"
      style={{ cursor: "pointer" }}
    >
      <div className="flex items-center justify-between whitespace-nowrap">
        <span className="text-sm">{title}</span>
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
