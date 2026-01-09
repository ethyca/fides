import { Skeleton } from "fidesui";

import { AsyncTreeNodeComponentProps } from "./types";

export const AsyncNodeSkeleton = ({ node }: AsyncTreeNodeComponentProps) =>
  <Skeleton paragraph={false} title={{ width: "80px" }} active>
    {typeof node.title === 'function' ? node.title(node) : node.title}
  </Skeleton>
