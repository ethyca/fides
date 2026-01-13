import { CopyTooltip, Flex, Text } from "fidesui";
import { lowerCase } from "lodash";

type LabeledProps = React.PropsWithChildren<{
  label: React.ReactNode;
  copyValue?: string | null;
}>;

export const LabeledText = ({ label, children, copyValue }: LabeledProps) => {
  const textContent = (
    <Text ellipsis={{ tooltip: true }} className="!max-w-60">
      {children}
    </Text>
  );

  return (
    <Flex gap="small" wrap>
      <Text type="secondary">{label}:</Text>
      {copyValue ? (
        <CopyTooltip
          contentToCopy={copyValue}
          copyText={`Copy ${lowerCase(label?.toString() ?? "")}`}
        >
          {textContent}
        </CopyTooltip>
      ) : (
        textContent
      )}
    </Flex>
  );
};
