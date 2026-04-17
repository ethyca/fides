/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import type { AccessPolicyChatResponse } from "~/features/access-policies/agent-chat.slice";

/**
 * Scripted 3-turn scenario for the access policy agent chat endpoint.
 * Tracks turn count per chat_history_id so repeated sends advance the script.
 */
export const agentChatHandlers = () => {
  const turnCounts = new Map<string, number>();

  const TURN_1_YAML = [
    "name: Third-Party Advertising — No Customer Data",
    "description: Deny use of customer contact and identifier data for third-party advertising",
    "enabled: true",
    "priority: 100",
    "decision: DENY",
    "match:",
    "  data_category:",
    "    any:",
    "      - user.contact",
    "      - user.unique_id",
    "  data_use:",
    "    any:",
    "      - marketing.advertising.third_party.targeted",
    "      - marketing.advertising.profiling",
    "action:",
    "  message: Access denied — customer data cannot be shared for third-party advertising",
  ].join("\n");

  const TURN_2_YAML = [
    "name: Third-Party Advertising — No Customer Data",
    "description: Deny use of customer contact and identifier data for third-party advertising unless the user has opted in to personalized advertising",
    "enabled: true",
    "priority: 100",
    "decision: DENY",
    "match:",
    "  data_category:",
    "    any:",
    "      - user.contact",
    "      - user.unique_id",
    "  data_use:",
    "    any:",
    "      - marketing.advertising.third_party.targeted",
    "      - marketing.advertising.profiling",
    "unless:",
    "  - type: consent",
    "    privacy_notice_key: advertising_opt_in",
    "    requirement: opt_in",
    "action:",
    "  message: Access denied — user has not opted in to personalized advertising",
  ].join("\n");

  const SCRIPTED_TURNS: Array<
    Omit<AccessPolicyChatResponse, "chat_history_id">
  > = [
    {
      message:
        "I've drafted a policy that denies third-party advertising access to customer contact and identifier data. It matches the `user.contact` and `user.unique_id` data categories against third-party targeted advertising and profiling data uses. Take a look in the editor.",
      new_policy_yaml: TURN_1_YAML,
    },
    {
      message:
        "Added a consent exception: access is allowed when the user has opted in to personalized advertising via the `advertising_opt_in` privacy notice. Without that opt-in, the rule stays DENY.",
      new_policy_yaml: TURN_2_YAML,
    },
    {
      message:
        "The policy now reflects the standard GDPR/CCPA pattern — block third-party advertising by default, allow only with explicit opt-in. Let me know if you want to scope it to a geography (e.g. EEA-only), add more data categories, or tighten the consent requirement.",
      new_policy_yaml: null,
    },
  ];

  return [
    // Return config with the agent chat feature flag enabled
    rest.get("*/api/v1/config", (_req, res, ctx) =>
      res(
        ctx.status(200),
        ctx.json({
          access_policies: {
            agent_enabled: true,
          },
        }),
      ),
    ),

    rest.post("*/api/v1/plus/llm/access-policy-chat", async (req, res, ctx) => {
      const body = await req.json();
      const chatHistoryId =
        (body.chat_history_id as string) ?? crypto.randomUUID();

      const turn = turnCounts.get(chatHistoryId) ?? 0;
      turnCounts.set(chatHistoryId, turn + 1);

      const scenario =
        SCRIPTED_TURNS[Math.min(turn, SCRIPTED_TURNS.length - 1)];

      // Simulate a short delay for realism
      return res(
        ctx.delay(800),
        ctx.status(200),
        ctx.json({
          chat_history_id: chatHistoryId,
          ...scenario,
        }),
      );
    }),
  ];
};
