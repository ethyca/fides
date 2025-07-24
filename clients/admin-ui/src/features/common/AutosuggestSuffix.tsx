import { AntTypography as Typography, GetProps } from "fidesui";

const { Text } = Typography;

interface AutosuggestSuffixProps extends GetProps<typeof Typography.Text> {
  searchText: string | undefined | null;
  suggestion: string | undefined | null;
}

/**
 * This component will be absolute positioned to the right of an
 * autosuggest input to act as suggestion completion. Wrap the input and
 * this component in a relative positioned container.
 *
 * @param searchText The text that was typed into the input
 * @param suggestion The suggestion to complete the searchText
 * @extends Typography.Text
 *
 * @example
 * ```tsx
 * <Box position="relative">
 *  <Input />
 *  <AutosuggestSuffix searchText={inputValue} suggestion={closestMatch} />
 * </Box>
 * ```
 */
export const AutosuggestSuffix = ({
  searchText,
  suggestion,
  ...props
}: AutosuggestSuffixProps) => {
  if (!searchText || !suggestion) {
    return null;
  }
  return (
    <Text
      aria-hidden
      style={{
        pointerEvents: "none",
        position: "absolute",
        zIndex: 10,
        top: "var(--ant-line-width)",
        bottom: "var(--ant-line-width)",
        left: "var(--ant-padding-sm)",
        lineHeight: "calc(var(--ant-control-height) - var(--ant-line-width))",
      }}
      {...props}
    >
      <Text className="text-transparent">{searchText}</Text>
      <Text type="secondary">{suggestion.substring(searchText.length)}</Text>
    </Text>
  );
};
