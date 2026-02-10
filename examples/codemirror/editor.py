"""Example: CodeMirror 6 editor component using starelements with import maps."""

from starhtml import H1, Button, Div, P, Pre, Script, Signal, Style, evt, serve, star_app

from starelements import Local, element

PYTHON_SNIPPET = """\
from starhtml import star_app, Div, H1, serve

app, rt = star_app()

@rt("/")
def home():
    return Div(
        H1("Hello, StarHTML!"),
        style="padding: 2rem;",
    )

serve()
"""

JS_SNIPPET = """\
import { effect, mergePatch, getPath } from 'datastar';

// Reactive counter using Datastar signals
mergePatch({ count: 0 });

effect(() => {
    const count = getPath('count');
    console.log(`Count is now: ${count}`);
});

// Increment every second
setInterval(() => {
    const current = getPath('count');
    mergePatch({ count: current + 1 });
}, 1000);
"""

# --- CodeMirror dependency maps ---
# unpkg serves raw ESM with bare imports internally (e.g., @lezer/common),
# so we must map ALL transitive dependencies for the browser to resolve them.

CM_IMPORT_MAP = {
    "@codemirror/state": "https://unpkg.com/@codemirror/state@6.4.1/dist/index.js",
    "@codemirror/view": "https://unpkg.com/@codemirror/view@6.28.1/dist/index.js",
    "@codemirror/language": "https://unpkg.com/@codemirror/language@6.10.1/dist/index.js",
    "@codemirror/commands": "https://unpkg.com/@codemirror/commands@6.5.0/dist/index.js",
    "@codemirror/autocomplete": "https://unpkg.com/@codemirror/autocomplete@6.16.0/dist/index.js",
    "@codemirror/search": "https://unpkg.com/@codemirror/search@6.5.6/dist/index.js",
    "@codemirror/lint": "https://unpkg.com/@codemirror/lint@6.8.1/dist/index.js",
    "@codemirror/lang-python": "https://unpkg.com/@codemirror/lang-python@6.1.6/dist/index.js",
    "@codemirror/lang-javascript": "https://unpkg.com/@codemirror/lang-javascript@6.2.2/dist/index.js",
    "@codemirror/theme-one-dark": "https://unpkg.com/@codemirror/theme-one-dark@6.1.2/dist/index.js",
    "@lezer/common": "https://unpkg.com/@lezer/common@1.2.1/dist/index.js",
    "@lezer/highlight": "https://unpkg.com/@lezer/highlight@1.2.0/dist/index.js",
    "@lezer/lr": "https://unpkg.com/@lezer/lr@1.4.0/dist/index.js",
    "@lezer/python": "https://unpkg.com/@lezer/python@1.1.14/dist/index.js",
    "@lezer/javascript": "https://unpkg.com/@lezer/javascript@1.4.14/dist/index.js",
    "style-mod": "https://unpkg.com/style-mod@4.1.0/src/style-mod.js",
    "w3c-keyname": "https://unpkg.com/w3c-keyname@2.2.8/index.js",
    "crelt": "https://unpkg.com/crelt@1.0.6/index.js",
}

CM_IMPORTS = {
    "state": "@codemirror/state",
    "view": "@codemirror/view",
    "language": "@codemirror/language",
    "commands": "@codemirror/commands",
    "highlight": "@lezer/highlight",
    "python": "@codemirror/lang-python",
    "javascript": "@codemirror/lang-javascript",
    "one_dark": "@codemirror/theme-one-dark",
}


@element("code-editor", height="320px", skeleton=True, imports=CM_IMPORTS, import_map=CM_IMPORT_MAP)
def CodeEditor():
    """CodeMirror 6 editor with theme/language switching."""
    value = Local("value", "")
    theme = Local("theme", "light")
    lang = Local("lang", "python")

    return Div(
        value,
        theme,
        lang,
        Script("""
            if (!state || !view || !commands || !language) {
                console.error('[CodeEditor] Failed to load dependencies');
                return;
            }

            const { EditorState, Compartment } = state;
            const { EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter, drawSelection } = view;
            const { defaultKeymap, history, historyKeymap } = commands;
            const { syntaxHighlighting, HighlightStyle } = language;
            const { tags } = highlight;

            const lightStyle = HighlightStyle.define([
                { tag: tags.keyword, color: '#d73a49' },
                { tag: tags.controlKeyword, color: '#d73a49', fontWeight: '500' },
                { tag: tags.definitionKeyword, color: '#d73a49' },
                { tag: tags.operatorKeyword, color: '#d73a49' },
                { tag: [tags.function(tags.variableName), tags.function(tags.definition(tags.variableName))], color: '#6f42c1' },
                { tag: tags.definition(tags.variableName), color: '#e36209' },
                { tag: tags.variableName, color: '#24292e' },
                { tag: [tags.className, tags.definition(tags.className)], color: '#6f42c1' },
                { tag: tags.propertyName, color: '#005cc5' },
                { tag: [tags.string, tags.special(tags.string)], color: '#032f62' },
                { tag: tags.number, color: '#005cc5' },
                { tag: tags.bool, color: '#005cc5' },
                { tag: tags.comment, color: '#6a737d', fontStyle: 'italic' },
                { tag: tags.operator, color: '#d73a49' },
                { tag: tags.punctuation, color: '#24292e' },
                { tag: tags.self, color: '#005cc5' },
                { tag: [tags.meta, tags.annotation], color: '#6f42c1' },
                { tag: tags.attributeName, color: '#6f42c1' },
                { tag: tags.typeName, color: '#6f42c1' },
            ]);

            const setupExtensions = [
                lineNumbers(),
                highlightActiveLineGutter(),
                history(),
                drawSelection(),
                highlightActiveLine(),
                keymap.of([...defaultKeymap, ...historyKeymap]),
                EditorView.lineWrapping,
                EditorView.theme({
                    "&": { height: "100%" },
                    ".cm-scroller": { overflow: "auto" }
                })
            ];

            const themeConfig = new Compartment();
            const langConfig = new Compartment();

            const getTheme = (t) => {
                if (t === 'dark' && one_dark) return one_dark.oneDark;
                return syntaxHighlighting(lightStyle);
            };

            const getLang = (l) => {
                if (l === 'javascript' && javascript) return javascript.javascript();
                if (l === 'python' && python) return python.python();
                return [];
            };

            const initialDoc = el.getAttribute('value') || '';
            const initialTheme = el.getAttribute('theme') || 'light';
            const initialLang = el.getAttribute('lang') || 'python';

            const view_inst = new EditorView({
                state: EditorState.create({
                    doc: initialDoc,
                    extensions: [
                        setupExtensions,
                        themeConfig.of(getTheme(initialTheme)),
                        langConfig.of(getLang(initialLang)),
                        EditorView.updateListener.of(update => {
                            if (update.docChanged) {
                                el.dispatchEvent(new CustomEvent('change', {
                                    detail: { value: update.state.doc.toString() },
                                    bubbles: true
                                }));
                            }
                        })
                    ]
                }),
                parent: refs('editor')
            });

            // Separate effects: theme/lang switching doesn't reset editor content
            effect(() => {
                view_inst.dispatch({
                    effects: [
                        themeConfig.reconfigure(getTheme($$theme)),
                        langConfig.reconfigure(getLang($$lang))
                    ]
                });
            });

            // Only update content when value signal changes externally (not from user typing)
            let lastExternalValue = initialDoc;
            effect(() => {
                const currentValue = $$value;
                if (currentValue !== undefined && currentValue !== lastExternalValue) {
                    lastExternalValue = currentValue;
                    const currentDoc = view_inst.state.doc.toString();
                    if (currentValue !== currentDoc) {
                        view_inst.dispatch({
                            changes: {from: 0, to: currentDoc.length, insert: currentValue}
                        });
                    }
                }
            });

            onCleanup(() => view_inst.destroy());
        """),
        Div(
            data_ref="editor",
            style="border: 1px solid #ccc; border-radius: 4px; overflow: hidden; height: 100%; text-align: left;",
        ),
        data_on_theme_change=("$$theme = evt.detail.value", {"trusted": True}),
        data_on_lang_change=("$$lang = evt.detail.value", {"trusted": True}),
        data_on_value_change=("$$value = evt.detail.value", {"trusted": True}),
        style="height: 100%;",
    )


app, rt = star_app()
app.register(CodeEditor)


@rt("/")
def home():
    return Div(
        (current_code := Signal("current_code", PYTHON_SNIPPET.strip())),
        (output := Signal("output", "")),
        (editor_theme := Signal("editor_theme", "light")),
        (editor_lang := Signal("editor_lang", "python")),
        Style("""
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

            *, *::before, *::after { box-sizing: border-box; }

            body {
                margin: 0;
                background: #f8f9fb;
                color: #1a1a2e;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }

            .demo-container {
                max-width: 860px;
                margin: 0 auto;
                padding: 48px 32px 64px;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }

            .demo-header {
                margin-bottom: 32px;
            }

            .demo-header h1 {
                font-size: 1.75rem;
                font-weight: 600;
                letter-spacing: -0.025em;
                color: #0f172a;
                margin: 0 0 6px 0;
            }

            .demo-header p {
                font-size: 0.925rem;
                color: #64748b;
                margin: 0;
                line-height: 1.5;
            }

            .editor-card {
                background: #fff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                overflow: hidden;
                box-shadow:
                    0 1px 3px rgba(0, 0, 0, 0.04),
                    0 4px 12px rgba(0, 0, 0, 0.03);
            }

            .toolbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 14px;
                background: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                gap: 12px;
            }

            .lang-group {
                display: flex;
                gap: 2px;
                background: #e2e8f0;
                border-radius: 8px;
                padding: 2px;
            }

            .btn {
                padding: 6px 14px;
                border: none;
                background: transparent;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                color: #64748b;
                transition: all 0.15s ease;
                line-height: 1.4;
            }

            .btn:hover {
                color: #1e293b;
                background: rgba(0, 0, 0, 0.04);
            }

            .btn.active {
                background: #fff;
                color: #0f172a;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
            }

            .btn-theme {
                padding: 6px 12px;
                border: 1px solid #e2e8f0;
                background: #fff;
                border-radius: 8px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                color: #475569;
                transition: all 0.15s ease;
            }

            .btn-theme:hover {
                background: #f1f5f9;
                border-color: #cbd5e1;
                color: #1e293b;
            }

            .editor-wrap {
                height: 320px;
            }

            .action-bar {
                display: flex;
                justify-content: flex-end;
                padding: 12px 14px;
                background: #f8fafc;
                border-top: 1px solid #e2e8f0;
            }

            .run-btn {
                padding: 8px 20px;
                border: none;
                background: #0f172a;
                color: #fff;
                border-radius: 8px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                transition: all 0.15s ease;
                letter-spacing: 0.01em;
            }

            .run-btn:hover {
                background: #1e293b;
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(15, 23, 42, 0.2);
            }

            .run-btn:active {
                transform: translateY(0);
                box-shadow: none;
            }

            .output-section {
                margin-top: 24px;
            }

            .output-label {
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: #94a3b8;
                margin: 0 0 8px 2px;
            }

            .terminal {
                background: #0f172a;
                color: #e2e8f0;
                font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
                font-size: 13px;
                line-height: 1.6;
                padding: 16px 20px;
                border-radius: 10px;
                min-height: 80px;
                overflow-x: auto;
                white-space: pre-wrap;
                word-break: break-word;
                border: 1px solid #1e293b;
                box-shadow:
                    0 2px 4px rgba(0, 0, 0, 0.08),
                    inset 0 1px 0 rgba(255, 255, 255, 0.03);
                margin: 0;
            }

            .terminal::before {
                content: "$ ";
                color: #38bdf8;
                font-weight: 500;
            }
        """),
        Div(
            H1("StarElements CodeMirror Demo"),
            P("A Python-native web component wrapping CodeMirror 6."),
            cls="demo-header",
        ),
        Div(
            Div(
                Div(
                    Button(
                        "Python",
                        data_on_click=current_code.set(PYTHON_SNIPPET.strip()) + "; " + editor_lang.set("python"),
                        cls="btn",
                        data_class_active=(editor_lang == "python"),
                    ),
                    Button(
                        "JavaScript",
                        data_on_click=current_code.set(JS_SNIPPET.strip()) + "; " + editor_lang.set("javascript"),
                        cls="btn",
                        data_class_active=(editor_lang == "javascript"),
                    ),
                    cls="lang-group",
                ),
                Button(
                    data_text=(editor_theme == "light").if_("Dark Mode", "Light Mode"),
                    data_on_click=(editor_theme == "light").if_(editor_theme.set("dark"), editor_theme.set("light")),
                    cls="btn-theme",
                ),
                cls="toolbar",
            ),
            CodeEditor(
                value=PYTHON_SNIPPET.strip(),
                data_attr_value=current_code,
                data_attr_theme=editor_theme,
                data_attr_lang=editor_lang,
                data_on_change=current_code.set(evt.detail.value),
                cls="editor-wrap",
            ),
            Div(
                Button("Run Code", data_on_click=output.set("Executing...\n\n" + current_code), cls="run-btn"),
                cls="action-bar",
            ),
            cls="editor-card",
        ),
        Div(
            P("Output", cls="output-label"),
            Pre(data_text=output, cls="terminal"),
            cls="output-section",
        ),
        cls="demo-container",
    )


if __name__ == "__main__":
    serve(port=8000)
