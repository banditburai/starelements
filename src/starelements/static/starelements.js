/**
 * starelements runtime - Web component bridge for Datastar
 *
 * Supports client-side rendering (clones template) and hydration (adopts server content).
 * Hydration detected via data-star-id attribute.
 *
 * Import maps for peer dependencies are generated server-side by starelements_hdrs().
 */

let instanceCounter = 0;

const toCamelCase = (s) => s.replace(/-([a-z])/g, (_, c) => c.toUpperCase());

const extractPrefixedAttrs = (el, prefix, valueFn = (v) => v) => {
    const result = {};
    for (const attr of el.attributes) {
        if (attr.name.startsWith(prefix)) {
            result[attr.name.slice(prefix.length)] = valueFn(attr.value);
        }
    }
    return result;
};

const parsers = {
    string: (v) => v,
    int: (v) => parseInt(v, 10),
    float: (v) => parseFloat(v),
    boolean: (v) => v === 'true' || v === '' || v === true,
    json: (v) => JSON.parse(v),
};

function parseCodec(codecStr) {
    let type = 'string', defaultStr = null;
    for (const part of codecStr.split('|')) {
        if (part in parsers) type = part;
        else if (part.startsWith('=')) defaultStr = part.slice(1);
    }
    const parse = parsers[type];
    return { type, parse, default: defaultStr !== null ? parse(defaultStr) : null };
}

export function initStarElements() {
    for (const template of document.querySelectorAll('template')) {
        const starAttr = Array.from(template.attributes).find(a => a.name.startsWith('data-star:'));
        if (starAttr) registerStarElement(starAttr.name.replace('data-star:', ''), template);
    }
}

function registerStarElement(name, template) {
    const signals = extractPrefixedAttrs(template, 'data-signal:', parseCodec);
    const imports = extractPrefixedAttrs(template, 'data-import:');
    const scripts = extractPrefixedAttrs(template, 'data-script:');  // UMD scripts

    const useShadow = template.hasAttribute('data-shadow-open') || template.hasAttribute('data-shadow-closed');
    const shadowMode = template.hasAttribute('data-shadow-closed') ? 'closed' : 'open';

    const setupCode = template.content.querySelector('script:not([data-static])')?.textContent ?? '';

    const staticScript = template.content.querySelector('script[data-static]');
    if (staticScript) {
        try { new Function(staticScript.textContent)(); }
        catch (e) { console.error(`[starelements] Static script error in ${name}:`, e); }
    }

    class StarElement extends HTMLElement {
        static observedAttributes = Object.keys(signals);

        constructor() {
            super();
            const serverId = this.getAttribute('data-star-id');
            this._namespace = serverId || `_star_${name.replace(/-/g, '_')}_id${instanceCounter++}`;
            this._hydrating = !!serverId;
            this._cleanups = [];
            this._imports = {};
            this._connected = false;
        }

        _namespaceSignalRefs(text) {
            return text.replace(/\$([a-z_][a-z0-9_]*)/gi, (_, sig) => `$${this._namespace}_${sig}`);
        }

        async connectedCallback() {
            await this._loadImports();
            this._signalValues = this._buildSignalValues();

            if (!this._hydrating) {
                const content = template.content.cloneNode(true);
                for (const s of content.querySelectorAll('script')) s.remove();
                this._rewriteSignals(content);
                this._prepopulateText(content);

                if (useShadow) {
                    this.attachShadow({ mode: shadowMode }).appendChild(content);
                } else {
                    this.appendChild(content);
                }
            }

            this._initSignals();
            this._runSetup(setupCode);
            this._triggerDatastarScan();
            this._connected = true;
            this.style.visibility = '';  // Clear inline style, CSS takes over
            this.setAttribute('data-star-ready', '');
        }

        disconnectedCallback() {
            for (const fn of this._cleanups) {
                try { fn(); } catch (e) { console.error(e); }
            }
            this._cleanups = [];
            this._removeSignals();
        }

        attributeChangedCallback(attrName, oldVal, newVal) {
            if (oldVal === newVal || !this._connected) return;
            const signalDef = signals[attrName];
            const fullName = `${this._namespace}_${toCamelCase(attrName)}`;
            window.__datastar_mergePatch?.({ [fullName]: signalDef ? signalDef.parse(newVal) : newVal });
        }

        async _loadImports() {
            // Load ESM imports via dynamic import()
            for (const [alias, url] of Object.entries(imports)) {
                if (!window[alias]) {
                    try {
                        const module = await import(url);
                        window[alias] = module.default || module;
                    } catch (e) {
                        console.error(`[starelements] Failed to load ${alias} from ${url}:`, e);
                    }
                }
                this._imports[alias] = window[alias];
            }

            // Load UMD scripts via script tag injection (for libraries with bundled deps)
            // Note: HTML attrs are lowercased, but UMD globals are often PascalCase
            const findGlobal = (name) => {
                const pascal = name.charAt(0).toUpperCase() + name.slice(1);
                return window[name] || window[pascal] || window[name.toUpperCase()];
            };
            for (const [alias, url] of Object.entries(scripts)) {
                if (!findGlobal(alias)) {
                    await new Promise((resolve, reject) => {
                        const script = document.createElement('script');
                        script.src = url;
                        script.onload = () => resolve();
                        script.onerror = () => reject(new Error(`Failed to load ${alias} from ${url}`));
                        document.head.appendChild(script);
                    }).catch(e => console.error(`[starelements] ${e.message}`));
                }
                this._imports[alias] = findGlobal(alias);
            }
        }

        _rewriteSignals(node) {
            const walk = (el) => {
                if (el.attributes) {
                    const renames = [];
                    for (const attr of el.attributes) {
                        // Namespace data-ref values so $refName signals match
                        if (attr.name === 'data-ref' && attr.value) {
                            attr.value = `${this._namespace}_${attr.value}`;
                        }
                        // Namespace data-computed attribute names and values
                        else if (attr.name.startsWith('data-computed:')) {
                            const signalName = attr.name.slice('data-computed:'.length);
                            const newName = `data-computed:${this._namespace}_${signalName}`;
                            const newValue = this._namespaceSignalRefs(attr.value);
                            renames.push([attr.name, newName, newValue]);
                        }
                        // Namespace $signal references in expressions
                        else if (attr.value.includes('$')) {
                            attr.value = this._namespaceSignalRefs(attr.value);
                        }
                    }
                    // Apply renames after iteration (can't modify during)
                    for (const [oldName, newName, newValue] of renames) {
                        el.removeAttribute(oldName);
                        el.setAttribute(newName, newValue);
                    }
                }
                el.childNodes?.forEach(walk);
            };
            walk(node);
        }

        _buildSignalValues() {
            const values = {};
            for (const [name, def] of Object.entries(signals)) {
                const attr = this.getAttribute(name);
                values[toCamelCase(name)] = attr !== null ? def.parse(attr) : def.default;
            }
            return values;
        }

        _prepopulateText(node) {
            const prefix = this._namespace + '_';
            for (const el of node.querySelectorAll('[data-text]')) {
                const match = el.getAttribute('data-text').match(/\$([a-z_][a-z0-9_]*)/i);
                if (match?.[1]?.startsWith(prefix)) {
                    const signalName = match[1].slice(prefix.length);
                    if (signalName in this._signalValues) {
                        el.textContent = String(this._signalValues[signalName]);
                    }
                }
            }
        }

        _initSignals() {
            const signalData = Object.fromEntries(
                Object.entries(this._signalValues).map(([k, v]) => [`${this._namespace}_${k}`, v])
            );
            this.setAttribute('data-signals', JSON.stringify(signalData));
        }

        _removeSignals() {
            const el = document.createElement('div');
            el.setAttribute('data-signals', JSON.stringify({ [this._namespace]: null }));
            el.style.display = 'none';
            document.body.appendChild(el);
            setTimeout(() => el.remove(), 0);
        }

        _runSetup(code) {
            if (!code.trim()) return;
            const actions = {};
            // Helper to get elements by ref name (accounts for namespacing)
            const refs = (refName) => this.querySelector(`[data-ref="${this._namespace}_${refName}"]`);
            try {
                new Function('el', 'onCleanup', 'actions', 'refs', ...Object.keys(this._imports), this._namespaceSignalRefs(code))(
                    this, (fn) => this._cleanups.push(fn), actions, refs, ...Object.values(this._imports)
                );
                this._actions = actions;
            } catch (e) {
                console.error(`[starelements] Setup error in ${name}:`, e);
            }
        }

        _triggerDatastarScan() {
            this.dispatchEvent(new CustomEvent('datastar:scan', { bubbles: true, detail: { root: this } }));
        }

        emit(eventName, detail) {
            this.dispatchEvent(new CustomEvent(eventName, { detail, bubbles: true, cancelable: true, composed: false }));
        }
    }

    customElements.define(name, StarElement);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStarElements);
} else {
    initStarElements();
}
