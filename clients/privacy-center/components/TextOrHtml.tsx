import { ChakraText as Text, ChakraTextProps as TextProps } from "fidesui";
import { ElementType } from "react";

import sanitizeHTML from "~/common/sanitize-html";

type TextOrHtmlProps = Omit<TextProps, "children"> & {
  allowHTMLDescription: boolean | null;
  children: string;
  component?: ElementType;
};

const TextOrHtml = ({
  allowHTMLDescription,
  children,
  component: Component = Text,
  ...props
}: TextOrHtmlProps) => {
  if (allowHTMLDescription) {
    return (
      <Component
        {...props}
        dangerouslySetInnerHTML={{
          __html: sanitizeHTML(children.trim()),
        }}
      />
    );
  }

  return <Component {...props}>{children}</Component>;
};

export default TextOrHtml;
