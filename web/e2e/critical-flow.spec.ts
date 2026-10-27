import { expect, test } from "@playwright/test";

test("employee has a multi-turn policy conversation and opens review queue", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "有依据、可复核的财务工作台" })).toBeVisible();
  await expect(page.locator("[data-nextjs-dialog]")).toHaveCount(0);
  await page.screenshot({ path: "test-results/home-workspace.png", fullPage: true });

  await page.goto("/policy");
  await page.getByLabel("制度问题").fill("上海出差住宿标准是什么？");
  await page.getByRole("button", { name: "发送" }).click();
  await expect(page.getByText("上海出差住宿标准是什么？", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "查看本轮完整记录" })).toBeVisible();

  await page.getByLabel("制度问题").fill("那北京呢？");
  await page.getByRole("button", { name: "发送" }).click();
  await expect(page.getByText("那北京呢？", { exact: true })).toBeVisible();
  expect(await page.getByRole("link", { name: "查看本轮完整记录" }).count()).toBe(2);

  await page.getByLabel("制度问题").fill("周末加班餐费一定可以报销吗？");
  await page.getByRole("button", { name: "发送" }).click();
  await expect(page.getByText("不能形成确定性结论，已进入财务复核。")).toBeVisible();

  await page.getByLabel("演示角色").selectOption("finance_reviewer");
  await page.goto("/reviews");
  await expect(page.getByRole("heading", { name: "人工复核队列" })).toBeVisible();
  await expect(page.getByText("加载待办…")).toBeHidden();
  expect(await page.getByRole("link", { name: "处理" }).count()).toBeGreaterThan(0);
  expect(pageErrors).toEqual([]);
});

test("finance user uploads and disables an external policy", async ({ page }) => {
  await page.goto("/knowledge");
  await page.getByLabel("制度文件").setInputFiles({
    name: "external-travel.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("# 外部差旅制度\n北京出差住宿标准为每晚 700 元。", "utf-8"),
  });
  await page.getByLabel("显示名称").fill("外部差旅制度 E2E");
  await page.getByRole("button", { name: "上传并发布" }).click();
  await expect(page.getByText("《外部差旅制度 E2E》已解析并发布到知识库。")).toBeVisible();

  const row = page.locator('[data-document-title="外部差旅制度 E2E"]');
  await expect(row.getByText("参与检索", { exact: true })).toBeVisible();
  await row.getByRole("button", { name: "停用" }).click();
  await expect(page.getByText("已停用", { exact: true })).toBeVisible();
});
