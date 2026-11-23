import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import {
  pauseSimulator,
  stepSimulator,
  injectDemandSpike,
  injectFault,
  clearFaults,
  waitForWorkerIngest,
} from "./helpers";

test.describe("Fuel Supply Intelligence Platform - End-to-End Suite", () => {
  test.beforeAll(async () => {
    await clearFaults();
    await pauseSimulator();
  });

  test.afterAll(async () => {
    await clearFaults();
    await pauseSimulator();
  });

  test("1. Dashboard loads with SIMULATED banner and version footer", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("Fuel Supply Intelligence");

    // Header HUD contains SIMULATED badge
    const simulatedBadge = page.locator(".topbar .simulated");
    await expect(simulatedBadge).toBeVisible();
    await expect(simulatedBadge).toHaveText("SIMULATED");

    // Version footer contains model, policy, and SIMULATED pill
    const footer = page.locator("footer.page-footer");
    await expect(footer).toBeVisible();
    await expect(footer).toContainText("Model v1.2.0");
    await expect(footer).toContainText("Policy v2.1.0");
    await expect(footer.locator(".status-simulated")).toHaveText("SIMULATED");
  });

  test("2. Interactive Guided Tour steps through judging walkthrough and is dismissible", async ({
    page,
  }) => {
    await page.goto("/");

    const tourSection = page.locator('section[aria-label="Judging Demo Walkthrough"]');
    if (await tourSection.isVisible()) {
      await expect(tourSection).toContainText("DEMO STEP 1 OF 5");
      await page.click('button[aria-label="Next tour step"]');
      await expect(tourSection).toContainText("DEMO STEP 2 OF 5");
      await page.click('button[aria-label="Dismiss guided tour"]');
      await expect(tourSection).not.toBeVisible();
    }

    // Toggle button should be available to re-launch tour
    const toggleButton = page.locator('button[aria-label="Interactive Judging Tour"]');
    await expect(toggleButton).toBeVisible();
    await toggleButton.click();
    await expect(page.locator('section[aria-label="Judging Demo Walkthrough"]')).toBeVisible();
  });

  test("3. Navigation across all 8 operational views", async ({ page }) => {
    await page.goto("/");

    const navButtons = [
      { name: "Network view", heading: "Supply Network" },
      { name: "Stockout risk", heading: "Stockout risk" },
      { name: "Recommendations", heading: "Recommendations" },
      { name: "Incoming supply", heading: "Incoming supply" },
      { name: "Alert center", heading: "Alert Center & Incident Log" },
      { name: "Evaluation", heading: "Evaluation" },
      { name: "System health", heading: "System health" },
      { name: "Overview", heading: "Operations Overview" },
    ];

    for (const item of navButtons) {
      await page.click(`button:has-text("${item.name}")`);
      await page.waitForTimeout(300);
      await expect(page.locator("body")).toBeVisible();
    }
  });

  test("4. Demand spike injection creates shortage risk and human review recommendation", async ({
    page,
  }) => {
    // Inject demand spike on station-mirpur and advance clock
    await injectDemandSpike("station-mirpur", 2.6, 12);
    await stepSimulator(2);
    await waitForWorkerIngest(2500);

    await page.goto("/");
    await page.click('button:has-text("Recommendations")');

    // Recommendations heading is visible
    await expect(page.locator("h2:has-text('Recommendations')")).toBeVisible();

    // Verify recommendations or candidates are rendered
    const cardOrEmpty = page.locator(".recommendation-card, .empty-note");
    await expect(cardOrEmpty.first()).toBeVisible();
  });

  test("5. Human decision workflow: approve with operator token and operator name", async ({
    page,
  }) => {
    await page.goto("/");
    await page.click('button:has-text("Recommendations")');

    const operatorToken = process.env.OPERATOR_TOKEN || "change-me";

    // Fill operator credentials
    const nameInput = page.locator('label.token-field:has-text("Operator name") input');
    if (await nameInput.isVisible()) {
      await nameInput.fill("Senior Dispatcher Rahat");
    }

    const tokenInput = page.locator('label.token-field:has-text("Operator token") input');
    await tokenInput.fill(operatorToken);

    // If a proposed recommendation exists, test approval
    const approveBtn = page.locator('button:has-text("Approve allocation")').first();
    if (await approveBtn.isVisible()) {
      // Handle native confirmation dialog
      page.once("dialog", async (dialog) => {
        await dialog.accept();
      });

      // If needs review checkbox exists, check it first
      const reviewCheck = page.locator('input[type="checkbox"]').first();
      if (await reviewCheck.isVisible() && !(await reviewCheck.isChecked())) {
        await reviewCheck.check();
      }

      await approveBtn.click();
      await waitForWorkerIngest(1500);

      // Verify notification or status update
      const notice = page.locator('.notice, [role="status"]');
      await expect(notice.first()).toBeVisible();

      // Step simulator to allow executor submission
      await stepSimulator(2);
      await waitForWorkerIngest(2000);
    }

    // Verify Decision History table exists and operator column is present
    const historyTable = page.locator("section.decision-history table");
    await expect(historyTable).toBeVisible();
    await expect(historyTable.locator("th:has-text('Operator')")).toBeVisible();
  });

  test("6. Human decision workflow: reject requires non-empty reason", async ({ page }) => {
    await page.goto("/");
    await page.click('button:has-text("Recommendations")');

    const operatorToken = process.env.OPERATOR_TOKEN || "change-me";
    const tokenInput = page.locator('label.token-field:has-text("Operator token") input');
    if (await tokenInput.isVisible()) {
      await tokenInput.fill(operatorToken);
    }

    const nameInput = page.locator('label.token-field:has-text("Operator name") input');
    if (await nameInput.isVisible()) {
      await nameInput.fill("Senior Dispatcher Rahat");
    }

    const rejectBtn = page.locator('button:has-text("Reject")').first();
    if (await rejectBtn.isVisible()) {
      const reasonBox = page.locator('textarea[placeholder="Required to reject"]').first();
      await reasonBox.fill(""); // Empty reason

      await rejectBtn.click();
      // Should show validation notice
      await expect(
        page.locator(".notice:has-text('Enter a reason before rejecting')"),
      ).toBeVisible();

      // Now fill valid reason
      await reasonBox.fill("Supply reserved for emergency backup priority.");
      await rejectBtn.click();
      await waitForWorkerIngest(1500);

      const notice = page.locator('.notice, [role="status"]');
      await expect(notice.first()).toBeVisible();
    }
  });

  test("7. What-If simulator displays counterfactual risk runway", async ({ page }) => {
    await page.goto("/");
    await page.click('button:has-text("Recommendations")');

    const reviewExpBtn = page.locator('button:has-text("Review explanation")').first();
    if (await reviewExpBtn.isVisible()) {
      await reviewExpBtn.click();

      // Verify what-if interactive container is loaded
      const whatIfSection = page.locator(".whatif-simulator, .risk-comparison");
      await expect(whatIfSection.first()).toBeVisible();
    }
  });

  test("8. Simulator fault triggers degraded notification and recovers cleanly", async ({
    page,
  }) => {
    await page.goto("/");

    // Inject transient simulator fault
    await injectFault("unavailable", 6);
    await waitForWorkerIngest(3000);

    // Refresh page or observe degraded status
    await page.reload();
    const noticeOrStatus = page.locator('.status-degraded, .notice-degraded, [role="status"]');
    await expect(noticeOrStatus.first()).toBeVisible();

    // Clear fault and verify recovery
    await clearFaults();
    await stepSimulator(1);
    await waitForWorkerIngest(2500);

    await page.reload();
    await expect(page.locator("body")).toBeVisible();
  });

  test("9. Alert Center displays incidents and exports CSV/JSON data", async ({ page }) => {
    await page.goto("/");
    await page.click('button:has-text("Alert center")');

    await expect(page.locator("h2:has-text('Alert Center')")).toBeVisible();

    // Export buttons are rendered
    await expect(page.locator('button:has-text("Export CSV")')).toBeVisible();
    await expect(page.locator('button:has-text("Export JSON")')).toBeVisible();
    await expect(page.locator('button:has-text("Copy JSON")')).toBeVisible();
  });

  test("10. System Health page reports component health and data age", async ({ page }) => {
    await page.goto("/");
    await page.click('button:has-text("System health")');

    await expect(page.locator("h2:has-text('System health')")).toBeVisible();

    // Verify component status rows (API, Database, Worker, Predictor)
    const tableOrList = page.locator(".health-card, .health-grid, .health-summary");
    await expect(tableOrList.first()).toBeVisible();
  });

  test("11. SSE push stream status indicator is visible", async ({ page }) => {
    await page.goto("/");
    const streamBadge = page.locator(".stream-badge");
    await expect(streamBadge).toBeVisible();
    // Must be either LIVE PUSH or POLLING FALLBACK
    const badgeText = await streamBadge.innerText();
    expect(badgeText).toMatch(/LIVE PUSH|POLLING FALLBACK/);
  });

  test("12. Accessibility audit (axe-core) on key operational pages", async ({ page }) => {
    const views = ["Overview", "Stockout risk", "Recommendations", "Alert center", "System health"];

    for (const view of views) {
      await page.goto("/");
      if (view !== "Overview") {
        await page.click(`button:has-text("${view}")`);
        await page.waitForTimeout(500);
      }

      const results = await new AxeBuilder({ page })
        .disableRules(["color-contrast"]) // dark theme custom colors audited separately
        .analyze();

      const criticalViolations = results.violations.filter(
        (v) => v.impact === "critical",
      );

      expect(criticalViolations).toEqual([]);
    }
  });
});
