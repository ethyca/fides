import type { TypographyProps } from "antd/lib";
import { Typography } from "antd/lib";

export interface CustomTypographyProps extends TypographyProps {
  children?: React.ReactNode;
}

export const withCustomProps = (WrappedComponent: typeof Typography) => {
  const WrappedTypography = ({ ...props }: CustomTypographyProps) => {
    return <WrappedComponent {...props} />;
  };

  // Preserve all Typography subcomponents
  WrappedTypography.Title = Typography.Title;
  WrappedTypography.Text = Typography.Text;
  WrappedTypography.Paragraph = Typography.Paragraph;
  WrappedTypography.Link = Typography.Link;

  return WrappedTypography;
};

export const CustomTypography = withCustomProps(Typography);
