import { Tab, TabProps } from "fidesui";
import { ReactNode } from "react";

export type TabListBorder = "full-width" | "partial";

export const FidesTab = ({
  label,
  isDisabled,
  ...other
}: {
  label: string | ReactNode;
  isDisabled?: boolean;
} & TabProps) => (
  <Tab
    data-testid={`tab-${label}`}
    _selected={{
      fontWeight: "600",
      color: "complimentary.500",
      borderColor: "complimentary.500",
    }}
    fontSize={other.fontSize}
    fontWeight="500"
    color="gray.500"
    isDisabled={isDisabled || false}
  >
    {label}
  </Tab>
);

export interface TabData {
  label: string;
  content: ReactNode | JSX.Element;
  isDisabled?: boolean;
}
