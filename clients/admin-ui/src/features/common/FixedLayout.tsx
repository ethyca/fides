import { Flex, FlexProps } from "fidesui";
import Head from "next/head";
import React from "react";

const FixedLayout = ({
  children,
  title,
  mainProps,
}: {
  children: React.ReactNode;
  title: string;
  mainProps?: FlexProps;
}) => (
  // NOTE: unlike the main Layout, this layout specifies a fixed height
  // of 100vh for the page, and overflow="auto" for the main content area. This
  // allows the content area to fitting the *viewport* height, which is a
  // special case layout needed by the datamap spatial & table views so that we
  // scroll within those elements instead of scrolling the overall page itself
  //
  // Ideally we could have one common layout used by *all* pages, but we couldn't
  // come up with a common method here without introducing other gotchas, so having
  // a slightly different layout was decided as the most maintainable option
  <Flex
    data-testid={title}
    direction="column"
    height="calc(100vh - 48px)"
    width="calc(100vw - 240px)"
  >
    <Head>
      <title>Fides Admin UI - {title}</title>
      <meta name="description" content="Privacy Engineering Platform" />
      <link rel="icon" href="/favicon.ico" />
    </Head>
    <Flex
      px={10}
      py={6}
      as="main"
      overflow="auto"
      direction="column"
      flex={1}
      minWidth={0}
      {...mainProps}
    >
      {children}
    </Flex>
  </Flex>
);
export default FixedLayout;
