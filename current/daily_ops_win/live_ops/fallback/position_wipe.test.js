"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { sizingOptions, widthForX, PositionWipePolicy } = require("./adaptive_wipe");
const options = sizingOptions({ mode: "x_position", min_width: 450, max_width: 600 });
const anchor = { positionX: 0, positionY: 0 };
const video = { baseWidth: 1920, baseHeight: 1080 };
const rect = (x, y, w = 300, h = 400) => ({ left: x, top: y, right: x+w, bottom: y+h });

test("X fitting uses BOX left edge only, not Y free space", () => {
  assert.equal(widthForX(rect(800, 0), anchor, video, options), 600);
  assert.equal(widthForX(rect(0, 600), anchor, video, options), 450);
  assert.equal(widthForX(rect(516, 0), anchor, video, options), 500);
  assert.equal(widthForX(rect(516, 600), anchor, video, options), 500);
  assert.equal(widthForX(rect(0, 0), anchor, video, options), 450);
});

test("equal-area BOXes produce different sizes based on position", () => {
  assert.equal(widthForX(rect(0, 0), anchor, video, options), 450);
  assert.equal(widthForX(rect(1000, 0), anchor, video, options), 600);
  assert.equal(widthForX(rect(0, 900), anchor, video, options), 450);
});

test("fitting preserves anchor, margin and canvas boundary", () => {
  const shifted = { positionX: 100, positionY: 50 };
  assert.equal(widthForX(rect(616, 50), shifted, video, options), 500);
  assert.equal(widthForX(rect(0, 0, 50, 20), shifted, video, options), 450);
  assert.equal(widthForX(rect(1916, 900), { positionX: 1400, positionY: 0 }, video, options), 500);
  assert.equal(widthForX(rect(0, 0), { positionX: 1600, positionY: 0 }, video, options), null);
  for (const r of [null, { empty: true }, rect(NaN, 0)]) {
    assert.equal(widthForX(r, anchor, video, options), null);
  }
});

test("shrink is immediate but smoothed, growth waits a clear second", () => {
  const p = new PositionWipePolicy();
  assert.equal(p.step(600, 100, 450, options), 450);
  assert.equal(p.step(600, 100.9, 450, options), 450);
  let width = p.step(600, 101, 450, options);
  assert.ok(width > 450 && width <= 466.0001);
  for (let i = 1; i < 100; i++) {
    const next = p.step(600, 101+i/10, width, options);
    assert.ok(next >= width && next-width <= 16.0001);
    width = next;
  }
  assert.equal(width, 600);
  const smaller = p.step(450, 111, width, options);
  assert.ok(smaller < 600 && smaller >= 584);
  assert.equal(p.target, 450);
  width = smaller;
  for (let i = 1; i < 100; i++) width = p.step(450, 111+i/10, width, options);
  assert.equal(width, 450);
});

test("brief space and invalid geometry cancel pending growth", () => {
  const p = new PositionWipePolicy();
  p.step(600, 100, 450, options);
  assert.equal(p.step(450, 100.8, 450, options), 450);
  assert.equal(p.step(600, 101, 450, options), 450);
  assert.equal(p.step(null, 101.5, 450, options), 450);
  assert.equal(p.target, null);
  assert.equal(p.step(600, 102, 450, options), 450);
  assert.equal(p.step(600, 102.9, 450, options), 450);
});
