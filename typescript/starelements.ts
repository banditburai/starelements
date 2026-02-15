/**
 * Signal scoping:
 *   $$signal - Component-local (namespaced per instance)
 *   $signal  - Global (page-level, passed through unchanged)
 */

import { effect, mergePatch, getPath } from "datastar";

type ParserFn = (v: string | boolean) => unknown;

interface SignalCodec {
  parse: ParserFn;
  default: unknown;
}

const globalWindow = window as unknown as Record<string, unknown>;

let instanceCounter = 0;

const toCamelCase = (s: string): string =>
  s.replace(/-([a-z])/g, (_, c: string) => c.toUpperCase());

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
    _cleanups: Array<() => void>;
    _imports: Record<string, unknown>;
    _connected: boolean;
    _signalValues!: Record<string, unknown>;

    constructor() {
      super();
      const serverId = this.getAttribute("data-star-id");
      this._namespace = serverId || `_star_${name.replace(/-/g, "_")}_id${instanceCounter++}`;
      this._hydrating = !!serverId;
      this._cleanups = [];
      this._imports = {};
      this._connected = false;
    }

    _namespaceSignalRefs(text: string): string {
      return text.replace(/\$\$([a-z_][a-z0-9_]*)/gi, (_, sig: string) => `$${this._namespace}_${sig}`);
    }

    async connectedCallback(): Promise<void> {
      try {
        await this._loadImports();
        if (!this.isConnected) return; // Disconnected during async import loading
        this._signalValues = this._buildSignalValues();

        if (!this._hydrating) {
          const content = template.content.cloneNode(true) as DocumentFragment;
          for (const s of content.querySelectorAll("script")) s.remove();
          this._rewriteSignals(content);

          if (useShadow) {
            this.attachShadow({ mode: shadowMode }).appendChild(content);
          } else {
            this.appendChild(content);
          }
        }

        this._initSignals();
        this._triggerDatastarScan();
        this._runSetup(setupCode);
      } catch (e) {
        console.error(`[starelements] connectedCallback error in <${name}>:`, e);
      } finally {
        this._connected = true;
        this.style.visibility = "";
        this.setAttribute("data-star-ready", "");
      }
    }

    disconnectedCallback(): void {
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

      const findGlobal = (alias: string): unknown => {
        const pascal = alias.charAt(0).toUpperCase() + alias.slice(1);
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
      const walk = (el: Node): void => {
        if ((el as Element).attributes) {
          const renames: Array<[string, string, string]> = [];
          for (const attr of (el as Element).attributes) {
            if (attr.name === "data-ref" && attr.value) {
              attr.value = `${this._namespace}_${attr.value}`;
            }
            else if (attr.name.startsWith("data-computed:")) {
              const signalName = attr.name.slice("data-computed:".length);
              const newName = `data-computed:${this._namespace}_${signalName}`;
              const newValue = this._namespaceSignalRefs(attr.value);
              renames.push([attr.name, newName, newValue]);
            }
            else if (attr.value.includes("$$")) {
              attr.value = this._namespaceSignalRefs(attr.value);
            }
          }
          for (const [oldName, newName, newValue] of renames) {
            (el as Element).removeAttribute(oldName);
            (el as Element).setAttribute(newName, newValue);
          }
        }
        for (const child of el.childNodes) walk(child);
      };
      walk(node);
    }

    _buildSignalValues(): Record<string, unknown> {
      const values: Record<string, unknown> = {};
      for (const [name, def] of Object.entries(signals)) {
        const attr = this.getAttribute(name);
        values[toCamelCase(name)] = attr !== null ? def.parse(attr) : def.default;
      }
      return values;
    }

    _initSignals(): void {
      const signalData: Record<string, unknown> = Object.fromEntries(
        Object.entries(this._signalValues).map(([k, v]) => [`${this._namespace}_${k}`, v])
      );
      mergePatch(signalData);
      // Escape @ and $ in strings to prevent Datastar's expression preprocessor
      // from mangling them ($foo → signal ref, @foo → action ref).
      // Using \uXXXX escapes inside JSON strings keeps them inert.
      const safeStringify = (s: string): string => {
        return JSON.stringify(s).replace(/[$@]/g, (ch) =>
          `\\u${ch.charCodeAt(0).toString(16).padStart(4, "0")}`
        );
      };
      const parts = Object.entries(signalData).map(([key, value]) => {
        const jsVal = typeof value === "string" && /[@$]/.test(value)
          ? safeStringify(value)
          : JSON.stringify(value);
        return `"${key}":${jsVal}`;
      });
      this.setAttribute("data-signals", `{${parts.join(",")}}`);
    }

    _removeSignals(): void {
      // null values delete keys per JSON Merge Patch (RFC 7386) semantics
      const patch: Record<string, null> = {};
      for (const name of Object.keys(signals)) {
        patch[`${this._namespace}_${toCamelCase(name)}`] = null;
      }
      mergePatch(patch);
    }

    _runSetup(code: string): void {
      if (!code.trim()) return;
      const refs = (refName: string): Element | null =>
        this.querySelector(`[data-ref="${this._namespace}_${refName}"]`);

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

      // Auto-capture effect dispose functions so they're cleaned up on disconnect
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

    // Web components insert DOM after Datastar's initial scan; re-trigger to process new data-* attrs
    _triggerDatastarScan(): void {
      this.dispatchEvent(new CustomEvent("datastar:scan", { bubbles: true, detail: { root: this } }));
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
