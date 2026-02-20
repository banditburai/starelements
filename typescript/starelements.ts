/**
 * Signal scoping:
 *   $$signal - Component-local (namespaced per instance)
 *   $signal  - Global (page-level, passed through unchanged)
 */

import { effect, mergePatch, getPath, beginBatch, endBatch } from "datastar";

type ParserFn = (v: string | boolean) => unknown;

interface SignalCodec {
  parse: ParserFn;
  default: unknown;
}

const globalWindow = window as unknown as Record<string, unknown>;

let instanceCounter = 0;

const toCamelCase = (s: string) =>
  s.replace(/-([a-z])/g, (_, c) => c.toUpperCase());

const extractPrefixedAttrs = (
  el: Element,
  prefix: string,
  valueFn: (v: string) => unknown = (v) => v,
): Record<string, unknown> => {
  const result: Record<string, unknown> = {};
  for (const attr of el.attributes) {
    if (attr.name.startsWith(prefix)) {
      result[attr.name.slice(prefix.length)] = valueFn(attr.value);
    }
  }
  return result;
};

const PARSERS: Record<string, ParserFn> = {
  string: (v) => v,
  int: (v) => parseInt(v as string, 10),
  float: (v) => parseFloat(v as string),
  boolean: (v) => v === "true" || v === "" || v === true,
  json: (v) => JSON.parse(v as string),
};

function parseCodec(codecStr: string): SignalCodec {
  let type = "string";
  let defaultStr: string | null = null;
  for (const part of codecStr.split("|")) {
    if (part in PARSERS) type = part;
    else if (part.startsWith("=")) defaultStr = part.slice(1);
  }
  const parse = PARSERS[type];
  return { parse, default: defaultStr !== null ? parse(defaultStr) : null };
}

export function initStarElements(): void {
  for (const template of document.querySelectorAll("template")) {
    const starAttr = Array.from(template.attributes).find(a => a.name.startsWith("data-star:"));
    if (starAttr) registerStarElement(starAttr.name.replace("data-star:", ""), template);
  }
}

function registerStarElement(name: string, template: HTMLTemplateElement): void {
  const signals = extractPrefixedAttrs(template, "data-signal:", parseCodec) as Record<string, SignalCodec>;
  const imports = extractPrefixedAttrs(template, "data-import:") as Record<string, string>;
  const scripts = extractPrefixedAttrs(template, "data-script:") as Record<string, string>;

  const useShadow = template.hasAttribute("data-shadow-open") || template.hasAttribute("data-shadow-closed");
  const shadowMode: ShadowRootMode = template.hasAttribute("data-shadow-closed") ? "closed" : "open";

  const setupCode = template.content.querySelector("script:not([data-static])")?.textContent ?? "";

  const staticScript = template.content.querySelector("script[data-static]");
  if (staticScript) {
    try { new Function(staticScript.textContent!)(); }
    catch (e) { console.error(`[starelements] Static script error in ${name}:`, e); }
  }

  class StarElement extends HTMLElement {
    static observedAttributes = Object.keys(signals);

    _namespace: string;
    _hydrating: boolean;
    _cleanups: Array<() => void> = [];
    _imports: Record<string, unknown> = {};
    _connected = false;
    _shadow: ShadowRoot | null;

    constructor() {
      super();
      const serverId = this.getAttribute("data-star-id");
      this._namespace = serverId || `_star_${name.replace(/-/g, "_")}_id${instanceCounter++}`;
      this._hydrating = !!serverId;
      this._shadow = useShadow ? this.attachShadow({ mode: shadowMode }) : null;
    }

    _namespaceSignalRefs(text: string): string {
      return text.replace(/\$\$([a-z_][a-z0-9_]*)/gi, (_, sig: string) => `$${this._namespace}_${sig}`);
    }

    async connectedCallback(): Promise<void> {
      try {
        await this._loadImports();
        if (!this.isConnected) return;
        const signalValues = this._buildSignalValues();

        if (!this._hydrating) {
          const content = template.content.cloneNode(true) as DocumentFragment;
          for (const s of content.querySelectorAll("script")) s.remove();
          this._rewriteSignals(content);
          (useShadow ? this._shadow! : this).appendChild(content);
        }

        // Batch the entire initialization so effects created by setup don't
        // fire until after the Datastar scan completes — matching how Datastar
        // batches its own initial page scan internally.
        beginBatch();
        try {
          this._initSignals(signalValues);
          this._runSetup(setupCode);
          this._triggerDatastarScan();
        } finally {
          endBatch();
        }

        this._connected = true;
        this.style.visibility = "";
        this.setAttribute("data-star-ready", "");
      } catch (e) {
        console.error(`[starelements] connectedCallback error in <${name}>:`, e);
      }
    }

    disconnectedCallback(): void {
      this._connected = false;
      for (const fn of this._cleanups) {
        try { fn(); } catch (e) { console.error(e); }
      }
      this._cleanups = [];
      this._removeSignals();
    }

    attributeChangedCallback(attrName: string, oldVal: string | null, newVal: string | null): void {
      if (oldVal === newVal || !this._connected) return;
      const signalDef = signals[attrName];
      const fullName = `${this._namespace}_${toCamelCase(attrName)}`;
      const parsed = newVal !== null && signalDef ? signalDef.parse(newVal) : newVal;
      mergePatch({ [fullName]: parsed });
    }

    async _loadImports(): Promise<void> {
      for (const [alias, url] of Object.entries(imports)) {
        if (!globalWindow[alias]) {
          try {
            globalWindow[alias] = await import(url);
          } catch (e) {
            console.error(`[starelements] Failed to load ${alias} from ${url}:`, e);
          }
        }
        this._imports[alias] = globalWindow[alias];
      }

      // Libraries expose globals inconsistently (e.g., Plotly vs plotly vs PIXI),
      // so check common casing variants.
      const findGlobal = (alias: string): unknown => {
        const pascal = alias[0].toUpperCase() + alias.slice(1);
        return globalWindow[alias] || globalWindow[pascal] || globalWindow[alias.toUpperCase()];
      };
      for (const [alias, url] of Object.entries(scripts)) {
        if (!findGlobal(alias)) {
          await new Promise<void>((resolve, reject) => {
            const script = document.createElement("script");
            script.src = url;
            script.onload = () => resolve();
            script.onerror = () => reject(new Error(`Failed to load ${alias} from ${url}`));
            document.head.appendChild(script);
          }).catch(e => console.error(`[starelements] ${(e as Error).message}`));
        }
        this._imports[alias] = findGlobal(alias);
      }
    }

    _rewriteSignals(node: Node): void {
      const COMPUTED = "data-computed:";
      const walk = (n: Node): void => {
        if (n.nodeType === Node.ELEMENT_NODE) {
          const el = n as Element;
          const renames: Array<[string, string, string]> = [];
          for (const attr of el.attributes) {
            if (attr.name === "data-ref" && attr.value) {
              attr.value = `${this._namespace}_${attr.value}`;
            }
            else if (attr.name.startsWith(COMPUTED)) {
              const signalName = attr.name.slice(COMPUTED.length);
              renames.push([attr.name, `${COMPUTED}${this._namespace}_${signalName}`, this._namespaceSignalRefs(attr.value)]);
            }
            else if (attr.value.includes("$$")) {
              attr.value = this._namespaceSignalRefs(attr.value);
            }
          }
          for (const [oldName, newName, newValue] of renames) {
            el.removeAttribute(oldName);
            el.setAttribute(newName, newValue);
          }
        }
        for (const child of n.childNodes) walk(child);
      };
      walk(node);
    }

    _buildSignalValues(): Record<string, unknown> {
      return Object.fromEntries(
        Object.entries(signals).map(([attr, def]) => {
          const val = this.getAttribute(attr);
          return [toCamelCase(attr), val !== null ? def.parse(val) : def.default];
        })
      );
    }

    _initSignals(signalValues: Record<string, unknown>): void {
      const signalData: Record<string, unknown> = Object.fromEntries(
        Object.entries(signalValues).map(([k, v]) => [`${this._namespace}_${k}`, v])
      );
      mergePatch(signalData);
      // Escape @ and $ in strings to prevent Datastar's expression preprocessor
      // from mangling them ($foo → signal ref, @foo → action ref).
      // Using \uXXXX escapes inside JSON strings keeps them inert.
      const safeStringify = (s: string) =>
        JSON.stringify(s).replace(/[$@]/g, (ch) =>
          `\\u${ch.charCodeAt(0).toString(16).padStart(4, "0")}`
        );
      const parts = Object.entries(signalData).map(([key, value]) => {
        const jsVal = typeof value === "string" && /[@$]/.test(value)
          ? safeStringify(value)
          : JSON.stringify(value);
        return `"${key}":${jsVal}`;
      });
      this.setAttribute("data-signals", `{${parts.join(",")}}`);
    }

    _removeSignals(): void {
      // null deletes keys per JSON Merge Patch (RFC 7386)
      mergePatch(Object.fromEntries(
        Object.keys(signals).map(s => [`${this._namespace}_${toCamelCase(s)}`, null])
      ));
    }

    _runSetup(code: string): void {
      if (!code.trim()) return;
      const queryRoot = useShadow ? this._shadow! : (this as Element);
      const refs = (refName: string): Element | null =>
        queryRoot.querySelector(`[data-ref="${this._namespace}_${refName}"]`);

      const namespace = this._namespace;
      const sp = new Proxy({} as Record<string | symbol, unknown>, {
        has: (target, prop) => {
          if (typeof prop === "string" && prop.startsWith("$$")) return true;
          return Reflect.has(target, prop);
        },
        get: (target, prop) => {
          if (typeof prop === "string" && prop.startsWith("$$")) {
            return getPath(`${namespace}_${prop.slice(2)}`);
          }
          return Reflect.get(target, prop);
        },
        set: (target, prop, value) => {
          if (typeof prop === "string" && prop.startsWith("$$")) {
            mergePatch({ [`${namespace}_${prop.slice(2)}`]: value });
            return true;
          }
          return Reflect.set(target, prop, value);
        }
      });

      const trackedEffect = (fn: () => void | (() => void)) => {
        const dispose = effect(fn);
        this._cleanups.push(dispose);
        return dispose;
      };

      try {
        // `with` provides $$signal scoping; works because new Function() runs in sloppy mode
        const wrappedCode = `with(sp) { ${code} }`;
        new Function(
          "el", "onCleanup", "refs", "effect", "sp", "datastar", ...Object.keys(this._imports),
          wrappedCode
        )(
          this, (fn: () => void) => this._cleanups.push(fn), refs,
          trackedEffect, sp, { effect: trackedEffect, mergePatch, getPath }, ...Object.values(this._imports)
        );
      } catch (e) {
        console.error(`[starelements] Setup error in ${name}:`, e);
      }
    }

    // Web components insert DOM after Datastar's initial scan; re-trigger to process new data-* attrs.
    _triggerDatastarScan(): void {
      const scanRoot = useShadow ? this._shadow! : this;
      this.dispatchEvent(new CustomEvent("datastar:scan", { bubbles: true, composed: true, detail: { root: scanRoot } }));
    }

    emit(eventName: string, detail?: unknown): void {
      this.dispatchEvent(new CustomEvent(eventName, { detail, bubbles: true, cancelable: true, composed: false }));
    }
  }

  customElements.define(name, StarElement);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initStarElements);
} else {
  initStarElements();
}

export default initStarElements;
