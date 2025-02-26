import { createCache, extractStyle, StyleProvider } from "@ant-design/cssinjs";
import type { DocumentContext } from "next/document";
import Document, { Head, Html, Main, NextScript } from "next/document";
import React from "react";

const MyDocument = () => (
  <Html lang="en">
    <Head />
    <body>
      <Main />
      <NextScript />
    </body>
  </Html>
);

// extract and inject antd's first-screen styles into HTML to avoid page flicker.
// see https://ant.design/docs/react/use-with-next#using-pages-router
MyDocument.getInitialProps = async (ctx: DocumentContext) => {
  const cache = createCache();
  const originalRenderPage = ctx.renderPage;
  // eslint-disable-next-line no-param-reassign
  ctx.renderPage = () =>
    originalRenderPage({
      enhanceApp: (App) => (props) => (
        <StyleProvider cache={cache}>
          <App {...props} />
        </StyleProvider>
      ),
    });

  const initialProps = await Document.getInitialProps(ctx);
  const style = extractStyle(cache, true);
  return {
    ...initialProps,
    styles: (
      <>
        {initialProps.styles}
        {/* eslint-disable-next-line react/no-danger */}
        <style dangerouslySetInnerHTML={{ __html: style }} />
      </>
    ),
  };
};

export default MyDocument;
