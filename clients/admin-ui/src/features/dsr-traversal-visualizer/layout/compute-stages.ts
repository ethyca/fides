import { PreviewEdge } from "../types";

const IDENTITY_ROOT_ID = "identity-root";

/**
 * Compute the stage (1-based topological depth from identity-root) of each
 * reach integration over the dependency edges. Orphans default to Stage 1.
 * `gates` edges are ignored — only `depends_on` carries traversal flow.
 */
export const computeStages = (
  reachNodeIds: string[],
  edges: PreviewEdge[],
): Record<string, number> => {
  const outgoing = new Map<string, string[]>();
  edges.forEach((e) => {
    if (e.kind !== "depends_on") {
      return;
    }
    const list = outgoing.get(e.source);
    if (list) {
      list.push(e.target);
    } else {
      outgoing.set(e.source, [e.target]);
    }
  });

  const reachSet = new Set(reachNodeIds);
  // depth starts undefined; BFS fills it. Orphans fall back to 1 at the end.
  const depth: Record<string, number | undefined> = {};

  const queue: string[] = [IDENTITY_ROOT_ID];
  const visitedAtDepth = new Map<string, number>();
  visitedAtDepth.set(IDENTITY_ROOT_ID, 0);

  while (queue.length > 0) {
    const u = queue.shift()!;
    const depthOfU = u === IDENTITY_ROOT_ID ? 0 : (depth[u] ?? 1);
    const targets = outgoing.get(u) ?? [];
    targets.forEach((v) => {
      if (!reachSet.has(v)) {
        return;
      }
      const candidate = depthOfU + 1;
      if (candidate > (depth[v] ?? 0)) {
        depth[v] = candidate;
        if (visitedAtDepth.get(v) !== candidate) {
          visitedAtDepth.set(v, candidate);
          queue.push(v);
        }
      }
    });
  }

  // Assign Stage 1 to any reach node that was never reached by a dep edge.
  const result: Record<string, number> = {};
  reachNodeIds.forEach((id) => {
    result[id] = depth[id] ?? 1;
  });

  return result;
};
