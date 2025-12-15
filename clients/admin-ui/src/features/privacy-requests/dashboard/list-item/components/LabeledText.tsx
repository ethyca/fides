import { AntFlex as Flex, AntText as Text, CopyTooltip } from "fidesui";
import { lowerCase } from "lodash";

type LabeledProps = React.PropsWithChildren<{
  label: React.ReactNode;
  copyValue?: string | null;
}>;

export const LabeledText = ({ label, children, copyValue }: LabeledProps) => (
  <Flex gap="small" wrap>
    <Text type="secondary">{label}:</Text>
    {copyValue && (
      <CopyTooltip
        contentToCopy={copyValue}
        copyText={`Copy ${lowerCase(label?.toString() ?? "")}`}
      >
        <Text ellipsis={{ tooltip: true }} className="!max-w-60">
          {children}
        </Text>
      </CopyTooltip>
    )}
    {!copyValue && (
      <Text ellipsis={{ tooltip: true }} className="!max-w-60">
        {children}
      </Text>
    )}
  </Flex>
);
