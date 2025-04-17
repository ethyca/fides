import type { TypographyProps } from "antd/lib";
import { Typography } from "antd/lib";
import classNames from "classnames";

import styles from "./CustomTypography.module.scss";

export interface CustomTypographyProps extends TypographyProps {
  children?: React.ReactNode;
}

// Custom wrapper for Paragraph to add paragraph role
const CustomParagraph = (
  props: React.ComponentProps<typeof Typography.Paragraph>,
) => {
  const { className, ...rest } = props;
  return (
    <Typography.Paragraph
      role="paragraph"
      className={classNames(styles.paragraph, className)}
      {...rest}
    />
  );
};

export const withCustomProps = (WrappedComponent: typeof Typography) => {
  const WrappedTypography = ({ ...props }: CustomTypographyProps) => {
    return <WrappedComponent {...props} />;
  };

  // Preserve all Typography subcomponents
  WrappedTypography.Title = Typography.Title;
  WrappedTypography.Text = Typography.Text;
  WrappedTypography.Paragraph = CustomParagraph;
  WrappedTypography.Link = Typography.Link;

  return WrappedTypography;
};

export const CustomTypography = withCustomProps(Typography);
