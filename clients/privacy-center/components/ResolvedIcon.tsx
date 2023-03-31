import * as mdIcons from "react-icons/md";
import * as faIcons from "react-icons/fa";
import { IconType } from "react-icons";
import { Icon, Image } from "@fidesui/react";

type ResolvedIconProps = {
  iconPath: string;
  iconBoxSize: string;
  description: string;
};

/**
 * IconProviders maps to the react-icons libraries supported by Fides.
 * The values of the enum elements are the prefix to indicate that the iconPath should use an icon library instead of a relative path or URL.
 */
enum IconProviders {
  MATERIALDESIGN = "md",
  FONTAWESOME = "fa",
}

const ResolvedIcon: React.FC<ResolvedIconProps> = ({
  iconPath,
  iconBoxSize,
  description,
}) => {
  const prefixCandidate = iconPath.toLowerCase().split(":")[0];
  const hasPrefix =
    Object.values<string>(IconProviders).includes(prefixCandidate);
  if (hasPrefix) {
    let iconType: IconType;
    switch (prefixCandidate) {
      case IconProviders.MATERIALDESIGN:
        iconType = mdIcons[iconPath.split(":")[1] as keyof typeof mdIcons];
        break;
      case IconProviders.FONTAWESOME:
        iconType = faIcons[iconPath.split(":")[1] as keyof typeof faIcons];
        break;
      default:
        iconType = faIcons.FaRegQuestionCircle;
        break;
    }
    return (
      <Icon as={iconType} boxSize={iconBoxSize} color="complimentary.500" />
    );
  }
  return <Image alt={description} boxSize={iconBoxSize} src={iconPath} />;
};

export default ResolvedIcon;
