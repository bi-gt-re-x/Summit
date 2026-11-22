/**
 * The paper look on the dashboard and the sidebar — styles/paper.css.
 *
 * Pinned: it's loaded on every page, every rule is scoped to signed-in pages
 * (`body.has-rail`) so the landing and sign-in pages keep their own look, and
 * the page ground is only taken over on the dashboard.
 */
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (path: string): string => readFileSync(new URL(path, import.meta.url), 'utf8');
const paper = read('./paper.css').replace(/\/\*[\s\S]*?\*\//g, '');
const main = read('../main.tsx');

/** Every selector outside @media, one per alternative. */
const selectors = [...paper.matchAll(/([^{}]+)\{/g)]
  .map((match) => match[1]!.trim())
  .filter((selector) => !selector.startsWith('@'))
  .flatMap((selector) => selector.split(','))
  .map((selector) => selector.trim())
  .filter(Boolean);

describe('the paper layer', () => {
  it('is loaded on every page, after the minimal layer', () => {
    const minimal = main.indexOf("import '@/styles/minimal.css';");
    const own = main.indexOf("import '@/styles/paper.css';");
    expect(minimal).toBeGreaterThan(-1);
    expect(own).toBeGreaterThan(minimal);
  });

  it('touches signed-in pages only', () => {
    expect(selectors.length).toBeGreaterThan(50);
    for (const selector of selectors) expect(selector).toMatch(/^html:root(\[[^\]]+\])? body\.has-rail/);
  });

  it('paints the page ground on the dashboard only', () => {
    const grounds = selectors.filter((selector) => /body\.has-rail(:has\(\.dash\))?$/.test(selector));
    const painted = grounds.filter((selector) => {
      const at = paper.indexOf(`${selector} {`);
      return at > -1 && /background:/.test(paper.slice(at, paper.indexOf('}', at)));
    });
    expect(painted).toEqual(['html:root body.has-rail:has(.dash)']);
  });
});
