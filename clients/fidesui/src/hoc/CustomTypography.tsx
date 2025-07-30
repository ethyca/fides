import type { TypographyProps } from "antd/lib";
import { Typography } from "antd/lib";
import classNames from "classnames";
import React from "react";

import styles from "./CustomTypography.module.scss";

type TextSize = "sm" | "default" | "lg";
type HeadingSize = 1 | 2 | 3 | 4 | 5;

interface CustomTypographyTextProps {
  size?: TextSize;
}

interface CustomTypographyTitleProps
  extends React.ComponentProps<typeof Typography.Title> {
  headingSize?: HeadingSize;
}

export interface CustomTypographyProps extends TypographyProps {
  children?: React.ReactNode;
  size?: TextSize;
}

const getTextSizeClassName = (size?: TextSize): string | undefined => {
  if (!size) {
    return undefined;
  }
  return styles[size];
};

const getHeadingSizeClassName = (size?: HeadingSize): string | undefined => {
  if (!size) {
    return undefined;
  }
  return styles[`h${size}`];
};

const CustomTitle = ({ headingSize, ...props }: CustomTypographyTitleProps) => (
  <Typography.Title
    className={getHeadingSizeClassName(headingSize)}
    {...props}
  />
);

const CustomText = ({
  size,
  ...props
}: React.ComponentProps<typeof Typography.Text> &
  CustomTypographyTextProps) => (
  <Typography.Text className={getTextSizeClassName(size)} {...props} />
);

const CustomParagraph = ({
  size,
  ...props
}: React.ComponentProps<typeof Typography.Paragraph> &
  CustomTypographyTextProps) => (
  <Typography.Paragraph
    role="paragraph"
    className={classNames(styles.paragraph, getTextSizeClassName(size))}
    {...props}
  />
);

const CustomLink = React.forwardRef<
  HTMLAnchorElement,
  React.ComponentProps<typeof Typography.Link> & CustomTypographyTextProps
>(({ size, ...props }, ref) => (
  <Typography.Link
    ref={ref}
    className={getTextSizeClassName(size)}
    {...props}
  />
));

CustomLink.displayName = "CustomLink";

type TypographyType = typeof Typography & {
  Text: typeof CustomText;
  Title: typeof CustomTitle;
  Paragraph: typeof CustomParagraph;
  Link: typeof CustomLink;
};

export const withCustomProps = (WrappedComponent: typeof Typography) => {
  const WrappedTypography = Object.assign(
    ({ size, ...props }: CustomTypographyProps) => (
      <WrappedComponent className={getTextSizeClassName(size)} {...props} />
    ),
    {
      Text: CustomText,
      Title: CustomTitle,
      Paragraph: CustomParagraph,
      Link: CustomLink,
    },
  ) as TypographyType;

  return WrappedTypography;
};

export const CustomTypography = withCustomProps(Typography);
