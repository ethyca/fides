import { Box, Flex } from "@fidesui/react";
import Head from "next/head";
import React from "react";

import Header from "~/features/common/Header";
import { NavSideBar } from "~/features/common/nav/v2/NavSideBar";
import { NavTopBar } from "~/features/common/nav/v2/NavTopBar";

const FixedLayout = ({
  children,
  title,
}: {
  children: React.ReactNode;
  title: string;
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
  // (see https://github.com/ethyca/fidesplus/pull/709)
  <Flex data-testid={title} direction="column" height="100vh">
    <Head>
      <title>Fides Admin UI - {title}</title>
      <meta name="description" content="Privacy Engineering Platform" />
      <link rel="icon" href="/favicon.ico" />
    </Head>
    <Header />
    <NavTopBar />
    <Flex
      as="main"
      overflow="auto"
      flexGrow={1}
      paddingTop={10}
      paddingLeft={10}
      gap={10}
    >
      <Box flex={0} flexShrink={0}>
        <NavSideBar />
      </Box>
      <Flex direction="column" flex={1} minWidth={0}>
        {children}
      </Flex>
    </Flex>
  </Flex>
);
export default FixedLayout;
