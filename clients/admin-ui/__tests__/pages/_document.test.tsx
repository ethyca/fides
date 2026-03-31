/**
 * @jest-environment node
 */

// Verify that the noindex meta tag is rendered in the document head to prevent search engine indexing.

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import MyDocument from "~/pages/_document";

jest.mock("next/document", () => ({
  Html: ({ children, ...props }: React.PropsWithChildren<object>) => (
    <html {...props}>{children}</html>
  ),
  Head: ({ children }: React.PropsWithChildren) => <head>{children}</head>,
  Main: () => <main />,
  NextScript: () => <script />,
  default: class Document {},
}));

jest.mock("@ant-design/cssinjs", () => ({
  createCache: jest.fn(() => ({})),
  extractStyle: jest.fn(() => ""),
  StyleProvider: ({ children }: React.PropsWithChildren) => children,
}));

describe("MyDocument", () => {
  it("renders noindex meta tag in the head", () => {
    const html = renderToStaticMarkup(<MyDocument />);
    expect(html).toContain('<meta name="robots" content="noindex"/>');
  });
});
