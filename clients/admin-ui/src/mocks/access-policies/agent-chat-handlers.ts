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
    "name: Marketing Data — EU Restriction",
    "description: Deny access to marketing data for EU users",
    "enabled: true",
    "priority: 100",
    "decision: DENY",
    "match:",
    "  data_use:",
    "    any:",
    "      - marketing.advertising.profiling",
    "      - marketing.communications.email",
    "      - marketing.advertising.third_party.targeted",
    "action:",
    "  message: Access denied — marketing data restricted for EU users",
  ].join("\n");

  const TURN_2_YAML = [
    "name: Marketing Data — EU Restriction",
    "description: Deny access to marketing data for EU users unless consent is provided",
    "enabled: true",
    "priority: 100",
    "decision: DENY",
    "match:",
    "  data_use:",
    "    any:",
    "      - marketing.advertising.profiling",
    "      - marketing.communications.email",
    "      - marketing.advertising.third_party.targeted",
    "unless:",
    "  - type: consent",
    "    privacy_notice_key: marketing_opt_in",
    "    requirement: opt_in",
    "  - type: geo_location",
    "    field: data_subject.geo_location",
    "    operator: not_in",
    "    values:",
    "      - eea",
    "action:",
    "  message: Access denied — marketing consent required for EU data subjects",
  ].join("\n");

  const SCRIPTED_TURNS: Array<
    Omit<AccessPolicyChatResponse, "chat_history_id">
  > = [
    {
      message:
        "I've created a policy that denies access to marketing and advertising data. It targets profiling, email marketing, and third-party targeted advertising data uses. You can now see the policy in the editor.",
      new_policy_yaml: TURN_1_YAML,
    },
    {
      message:
        "Done! I've added two exceptions: the policy now allows access when the user has opted in to the `marketing_opt_in` privacy notice, and it exempts non-EEA data subjects via a geo-location constraint.",
      new_policy_yaml: TURN_2_YAML,
    },
    {
      message:
        "The current policy looks solid. It covers the main marketing data uses with consent and geo-location exceptions. Let me know if you'd like to adjust the priority, add more data uses, or modify the action message.",
      new_policy_yaml: null,
    },
  ];

  return [
    // Return config with the agent chat feature flag enabled
    rest.get("*/api/v1/config", (_req, res, ctx) =>
      res(
        ctx.status(200),
        ctx.json({
          detection_discovery: {
            access_policy_agent_enabled: true,
            llm_classifier_enabled: true,
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
