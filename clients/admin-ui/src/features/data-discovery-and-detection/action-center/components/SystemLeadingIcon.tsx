import { Badge, Icons, SparkleIcon } from "fidesui";

import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";

import {
  getMockSystemLogoSource,
  isNewSystem,
  isSuggestedSystem,
} from "../mock/mockCloudInfraSystems";

const ICON_SIZE = 18;
const BRAND_STYLE = { color: "var(--fidesui-brand-minos)" };

/**
 * Generic system icon, with a small green "new" dot for user-created systems
 * (systems not matched to Compass/inventory or a suggestion).
 */
const GenericSystemIcon = ({ value }: { value?: string | number | null }) => {
  const icon = (
    <Icons.TransformInstructions className="flex-none" style={BRAND_STYLE} />
  );
  return isNewSystem(value) ? (
    <Badge dot color="green" offset={[-2, 2]} className="flex-none">
      {icon}
    </Badge>
  ) : (
    icon
  );
};

/**
 * Leading icon for the explorer tree and assign dropdown: the connector logo
 * for known Compass/inventory systems, otherwise the generic system icon
 * (with a green "new" dot for user-created systems). Suggested systems are not
 * specially marked here — that distinction lives on the resource tags.
 */
export const SystemLeadingIcon = ({
  value,
}: {
  value?: string | number | null;
}) => {
  const logoSource = getMockSystemLogoSource(value);
  if (logoSource) {
    return (
      <ConnectionTypeLogo
        data={logoSource}
        size={ICON_SIZE}
        className="flex-none"
      />
    );
  }
  return <GenericSystemIcon value={value} />;
};

/**
 * Leading icon for the assigned-system tags on a resource: a sparkle for
 * Fides-suggested systems, otherwise the generic system icon (with a green
 * "new" dot for user-created systems).
 */
export const SystemTagIcon = ({
  value,
}: {
  value?: string | number | null;
}) => {
  if (isSuggestedSystem(value)) {
    return <SparkleIcon className="flex-none" style={BRAND_STYLE} />;
  }
  return <GenericSystemIcon value={value} />;
};
