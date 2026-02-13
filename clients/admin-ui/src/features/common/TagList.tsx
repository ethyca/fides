import { Tag, TagProps } from "fidesui";
import { ReactNode } from "react";

export interface TagListProps {
  /**
   * Array of tag items to display. Can be strings or objects with value/label.
   */
  tags: string[] | Array<{ value: string; label?: ReactNode }>;
  /**
   * Maximum number of tags to display before showing "+N" overflow indicator.
   * @default 2
   */
  maxTags?: number;
  /**
   * Props to pass to each Tag component.
   */
  tagProps?: TagProps;
  /**
   * Props to pass to the overflow "+N" Tag component.
   */
  overflowTagProps?: TagProps;
  /**
   * Custom render function for each tag.
   * Receives the tag value/object and index.
   */
  renderTag?: (
    tag: string | { value: string; label?: ReactNode },
    index: number,
  ) => ReactNode;
  /**
   * Class name for the container span.
   */
  className?: string;
}

/**
 * A simple component that displays a list of tags with optional overflow indicator.
 * Shows first N tags and a "+X" tag if there are more.
 *
 * @example
 * ```tsx
 * <TagList tags={["tag1", "tag2", "tag3"]} maxTags={2} />
 * // Renders: <tag1> <tag2> <+1>
 * ```
 */
export const TagList = ({
  tags,
  maxTags = 2,
  tagProps,
  overflowTagProps,
  renderTag,
  className,
}: TagListProps) => {
  if (!tags || tags.length === 0) {
    return null;
  }

  const visibleTags = tags.slice(0, maxTags);
  const remainingCount = tags.length - maxTags;

  return (
    <span className={className}>
      {visibleTags.map((tag, index) => {
        const tagValue = typeof tag === "string" ? tag : tag.value;
        const tagLabel =
          typeof tag === "string" ? tag : (tag.label ?? tag.value);

        if (renderTag) {
          return <span key={tagValue}>{renderTag(tag, index)}</span>;
        }

        return (
          <span key={tagValue}>
            <Tag {...tagProps}>{tagLabel}</Tag>
            {index < visibleTags.length - 1 && " "}
          </span>
        );
      })}
      {remainingCount > 0 && (
        <>
          {" "}
          <Tag color="corinth" {...overflowTagProps}>
            +{remainingCount}
          </Tag>
        </>
      )}
    </span>
  );
};
