/**
 * starelements runtime - Web component bridge for Datastar
 *
 * Processes <template data-star:component-name> elements and registers
 * custom elements with proper signal scoping and lifecycle management.
 */

// Instance counter for unique IDs
let instanceCounter = 0;

/**
 * Initialize all starelements on the page.
 * Call this after DOM is ready.
 */
export function initStarElements() {
    // Find all template elements with data-star:* attribute
    const templates = document.querySelectorAll('template[data-star\\:]');

    templates.forEach(template => {
        // Extract component name from data-star:name attribute
        const attrs = Array.from(template.attributes);
        const starAttr = attrs.find(a => a.name.startsWith('data-star:'));
        if (!starAttr) return;

        const componentName = starAttr.name.replace('data-star:', '');
        registerStarElement(componentName, template);
    });
}

/**
 * Register a custom element from a template.
 */
function registerStarElement(name, template) {
    // Parse props from data-props:* attributes
    const props = {};
    Array.from(template.attributes).forEach(attr => {
        if (attr.name.startsWith('data-props:')) {
            const propName = attr.name.replace('data-props:', '');
            props[propName] = parseCodec(attr.value);
        }
    });

    // Parse imports from data-import:* attributes
    const imports = {};
    Array.from(template.attributes).forEach(attr => {
        if (attr.name.startsWith('data-import:')) {
            const alias = attr.name.replace('data-import:', '');
            imports[alias] = attr.value;
        }
    });

    // Check for shadow DOM
    const useShadow = template.hasAttribute('data-shadow-open') ||
                      template.hasAttribute('data-shadow-closed');
    const shadowMode = template.hasAttribute('data-shadow-closed') ? 'closed' : 'open';

    // Extract setup script
    const scriptEl = template.content.querySelector('script:not([data-static])');
    const setupCode = scriptEl ? scriptEl.textContent : '';

    // Extract static script (runs once)
    const staticScriptEl = template.content.querySelector('script[data-static]');
    const staticCode = staticScriptEl ? staticScriptEl.textContent : '';

    // Run static code once
    if (staticCode) {
        try {
            new Function(staticCode)();
        } catch (e) {
            console.error(`[starelements] Static script error in ${name}:`, e);
        }
    }

    // Define custom element class
    class StarElement extends HTMLElement {
        static observedAttributes = Object.keys(props);

        constructor() {
            super();
            this._id = `id${instanceCounter++}`;
            this._namespace = `_star.${name.replace(/-/g, '_')}.${this._id}`;
            this._cleanups = [];
            this._imports = {};
        }

        async connectedCallback() {
            // Load imports
            await this._loadImports();

            // Clone template content
            const content = template.content.cloneNode(true);

            // Remove script elements from content
            content.querySelectorAll('script').forEach(s => s.remove());

            // Rewrite $signals to namespaced paths
            this._rewriteSignals(content);

            // Initialize signals in Datastar store
            this._initSignals();

            // Attach content
            if (useShadow) {
                const shadow = this.attachShadow({ mode: shadowMode });
                shadow.appendChild(content);
            } else {
                this.appendChild(content);
            }

            // Run setup script
            this._runSetup(setupCode);

            // Trigger Datastar to process new elements
            this._triggerDatastarScan();
        }

        disconnectedCallback() {
            // Run cleanup functions
            this._cleanups.forEach(fn => {
                try { fn(); } catch (e) { console.error(e); }
            });
            this._cleanups = [];

            // Remove signals from store
            this._removeSignals();
        }

        attributeChangedCallback(attrName, oldVal, newVal) {
            if (oldVal === newVal) return;

            // Update corresponding signal
            const camelName = attrName.replace(/-([a-z])/g, (_, c) => c.toUpperCase());

            // Parse value according to prop type
            const propDef = props[attrName];
            const parsedValue = propDef ? propDef.parse(newVal) : newVal;

            // Set signal value (Datastar integration point)
            this._setSignal(camelName, parsedValue);
        }

        async _loadImports() {
            for (const [alias, url] of Object.entries(imports)) {
                if (!window[alias]) {
                    try {
                        const module = await import(url);
                        window[alias] = module.default || module;
                        this._imports[alias] = window[alias];
                    } catch (e) {
                        console.error(`[starelements] Failed to load ${alias} from ${url}:`, e);
                    }
                } else {
                    this._imports[alias] = window[alias];
                }
            }
        }

        _rewriteSignals(node) {
            const namespace = this._namespace;

            const walk = (el) => {
                if (el.attributes) {
                    Array.from(el.attributes).forEach(attr => {
                        if (attr.value.includes('$')) {
                            // Rewrite $foo to $._star.component.id.foo
                            // But preserve $$global (double dollar for globals)
                            attr.value = attr.value.replace(
                                /\$([a-z_][a-z0-9_]*)/gi,
                                (match, name) => `$${namespace}.${name}`
                            );
                        }
                    });
                }
                if (el.childNodes) {
                    el.childNodes.forEach(walk);
                }
            };

            walk(node);
        }

        _initSignals() {
            // Initialize prop signals from attributes
            Object.keys(props).forEach(propName => {
                const camelName = propName.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
                const attrValue = this.getAttribute(propName);
                const propDef = props[propName];
                const value = attrValue !== null ?
                    propDef.parse(attrValue) :
                    propDef.default;
                this._setSignal(camelName, value);
            });
        }

        _setSignal(name, value) {
            // Create nested signal path in Datastar store
            // This creates $._star.component_name.id0.signalName
            const path = `${this._namespace}.${name}`;

            // Use Datastar's signal initialization if available
            // Otherwise, fall back to creating a data-signals element
            const signalEl = document.createElement('div');
            signalEl.setAttribute('data-signals', JSON.stringify({
                [path.replace(/\./g, '_')]: value
            }));
            signalEl.style.display = 'none';
            document.body.appendChild(signalEl);

            // Remove after Datastar processes it
            setTimeout(() => signalEl.remove(), 0);
        }

        _removeSignals() {
            // Set namespace to null to remove signals
            const signalEl = document.createElement('div');
            signalEl.setAttribute('data-signals', JSON.stringify({
                [this._namespace.replace(/\./g, '_')]: null
            }));
            signalEl.style.display = 'none';
            document.body.appendChild(signalEl);
            setTimeout(() => signalEl.remove(), 0);
        }

        _runSetup(code) {
            if (!code.trim()) return;

            const namespace = this._namespace;
            const el = this;
            const importRefs = this._imports;

            // Create helpers available in setup scope
            const onCleanup = (fn) => this._cleanups.push(fn);

            // Rewrite $signals in setup code
            const rewrittenCode = code.replace(
                /\$([a-z_][a-z0-9_]*)/gi,
                (match, name) => `$${namespace}.${name}`
            );

            // Create actions object for component methods
            const actions = {};

            try {
                // Execute setup in sandboxed scope
                const setupFn = new Function(
                    'el', 'onCleanup', 'actions', ...Object.keys(importRefs),
                    rewrittenCode
                );
                setupFn(el, onCleanup, actions, ...Object.values(importRefs));

                // Attach actions to element for @action() calls
                this._actions = actions;
            } catch (e) {
                console.error(`[starelements] Setup error in ${name}:`, e);
            }
        }

        _triggerDatastarScan() {
            // Dispatch event that Datastar listens for to rescan DOM
            // This ensures new data-* attributes are processed
            const event = new CustomEvent('datastar:scan', {
                bubbles: true,
                detail: { root: this }
            });
            this.dispatchEvent(event);
        }

        // Helper to emit events
        emit(eventName, detail) {
            this.dispatchEvent(new CustomEvent(eventName, {
                detail,
                bubbles: true,
                cancelable: true,
                composed: false
            }));
        }
    }

    // Register the custom element
    customElements.define(name, StarElement);
}

/**
 * Parse a Datastar codec string into a prop definition.
 */
function parseCodec(codecStr) {
    const parts = codecStr.split('|');
    const def = {
        type: 'string',
        default: null,
        required: false,
        min: null,
        max: null,
        parse: (v) => v
    };

    parts.forEach(part => {
        if (['string', 'int', 'float', 'boolean', 'json'].includes(part)) {
            def.type = part;
        } else if (part.startsWith('min:')) {
            def.min = parseFloat(part.slice(4));
        } else if (part.startsWith('max:')) {
            def.max = parseFloat(part.slice(4));
        } else if (part === 'required!') {
            def.required = true;
        } else if (part.startsWith('=')) {
            def.default = part.slice(1);
        }
    });

    // Create parser based on type
    switch (def.type) {
        case 'int':
            def.parse = (v) => {
                const n = parseInt(v, 10);
                if (def.min !== null) return Math.max(def.min, n);
                if (def.max !== null) return Math.min(def.max, n);
                return n;
            };
            if (def.default) def.default = parseInt(def.default, 10);
            break;
        case 'float':
            def.parse = (v) => {
                const n = parseFloat(v);
                if (def.min !== null) return Math.max(def.min, n);
                if (def.max !== null) return Math.min(def.max, n);
                return n;
            };
            if (def.default) def.default = parseFloat(def.default);
            break;
        case 'boolean':
            def.parse = (v) => v === 'true' || v === '' || v === true;
            if (def.default) def.default = def.default === 'true';
            break;
        case 'json':
            def.parse = (v) => JSON.parse(v);
            if (def.default) def.default = JSON.parse(def.default);
            break;
    }

    return def;
}

// Auto-initialize on DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStarElements);
} else {
    initStarElements();
}
