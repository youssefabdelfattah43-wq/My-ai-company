import test from "node:test";
import assert from "node:assert/strict";
import { routeTask, approvalRequired } from "../src/index.js";

test("SI NATURAL task routes to the intended specialist", () => {
  assert.equal(routeTask("content_creation"), "creative");
  assert.equal(routeTask("campaign_analysis"), "media_buyer");
  assert.equal(routeTask("competitor_analysis"), "research");
  assert.equal(routeTask("profit_report"), "operations");
});
test("unknown task types are rejected", () => {
  assert.throws(() => routeTask("unknown_action"), /Unsupported/);
});
test("sensitive actions require CEO approval", () => {
  for (const action of ["campaign_publishing", "budget_changes", "price_changes", "bulk_messages", "refunds", "external_account_changes"]) {
    assert.equal(approvalRequired(action), true);
  }
  assert.equal(approvalRequired("read_ad_reports"), false);
});
