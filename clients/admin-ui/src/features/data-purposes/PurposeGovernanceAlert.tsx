import { Alert, Button, ConfigProvider, Flex, Icons, SparkleIcon, Tag, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo } from "react";

import type { DataPurpose, PurposeDatasetAssignment } from "./types";

interface PurposeGovernanceAlertProps {
  purpose: DataPurpose;
  datasets: PurposeDatasetAssignment[];
  onAcceptCategories: (categories: string[]) => void;
}

/**
 * AI-styled governance alert describing drift between defined and detected
 * categories on the purpose. Uses the Alert message + description pattern so
 * the banner breathes like the larger alert style used elsewhere.
 * Dismissable via the built-in Alert close control.
 */
const PurposeGovernanceAlert = ({
  purpose,
  datasets,
  onAcceptCategories,
}: PurposeGovernanceAlertProps) => {
  // The purpose detail page isn't currently wrapped in a ThemeModeProvider,
  // so hard-code to the light-mode tokens rather than using `useThemeMode`.
  const alertTheme = useMemo(
    () => ({
      components: {
        Alert: {
          colorInfoBg: palette.FIDESUI_LIMESTONE,
          colorInfoBorder: palette.FIDESUI_LIMESTONE,
          withDescriptionPadding: "16px 20px",
          fontSize: 14,
        },
      },
    }),
    [],
  );

  const definedSet = useMemo(
    () => new Set(purpose.data_categories),
    [purpose.data_categories],
  );

  const undeclared = useMemo(() => {
    const seen = new Set<string>();
    datasets.forEach((d) => {
      d.data_categories.forEach((c) => {
        if (!definedSet.has(c)) seen.add(c);
      });
    });
    return Array.from(seen);
  }, [datasets, definedSet]);

  // Systems that contribute at least one undeclared category.
  const contributingSystems = useMemo(() => {
    const names = new Set<string>();
    datasets.forEach((d) => {
      if (d.data_categories.some((c) => !definedSet.has(c))) {
        names.add(d.system_name);
      }
    });
    return Array.from(names);
  }, [datasets, definedSet]);

  // Also consider purpose-level detected categories in case the roll-up lives
  // there rather than on individual dataset assignments.
  const additionalUndeclared = useMemo(
    () =>
      purpose.detected_data_categories.filter(
        (c) => !definedSet.has(c) && !undeclared.includes(c),
      ),
    [purpose.detected_data_categories, definedSet, undeclared],
  );

  const allUndeclared = [...undeclared, ...additionalUndeclared];

  if (allUndeclared.length === 0) {
    return null;
  }

  return (
    <ConfigProvider theme={alertTheme}>
      <Alert
        type="info"
        showIcon
        icon={<SparkleIcon size={16} />}
        closable
        style={{ padding: "16px 20px", alignItems: "flex-start" }}
        message={<b>Governance insight</b>}
        description={
          <Flex align="center" gap={8} style={{ marginTop: 4 }}>
            <span style={{ lineHeight: 1.6 }}>
              {allUndeclared.length}{" "}
              {allUndeclared.length === 1 ? "category was" : "categories were"}{" "}
              detected in{" "}
              {contributingSystems.length > 0 ? (
                <>
                  {contributingSystems.map((s, i) => (
                    <span key={s}>
                      {i > 0 && ", "}
                      {s}
                    </span>
                  ))}{" "}
                </>
              ) : null}
              that{" "}
              {allUndeclared.length === 1 ? "is not" : "are not"} defined on this
              purpose.
            </span>
            <Button
              size="small"
              type="text"
              icon={<Icons.Checkmark size={14} />}
              onClick={() => onAcceptCategories(allUndeclared)}
              style={{ whiteSpace: "nowrap" }}
            >
              Approve {allUndeclared.length === 1 ? "category" : "categories"}
            </Button>
          </Flex>
        }
      />
    </ConfigProvider>
  );
};

export default PurposeGovernanceAlert;
