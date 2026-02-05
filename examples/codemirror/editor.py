from starhtml import star_app, Div, Button, Signal, H1, P, Pre, Style, evt
from starelements import element, ComponentSignal

@element("code-editor", height="300px", skeleton=True)
class CodeEditor:
    """
    A CodeMirror 6 based code editor component.

    Uses ComponentSignal for component-local state ($$value, $$theme, $$lang).
    In setup(), use $$ for local and $ for global signals.
    """
    
    # UNPKG Strategy: Manual Dependency Resolution
    # We use unpkg raw ESM files which have bare imports internally (e.g., @lezer/common).
    # This requires mapping ALL dependencies in import_map for the browser to resolve them.
    #
    # For simpler cases with bundled/self-contained ESM modules, you can skip import_map
    # and use URLs directly in imports:
    #   imports = {"chart": "https://cdn.jsdelivr.net/npm/chart.js/+esm"}

    _STATE_VER = "6.4.1"
    _VIEW_VER = "6.28.1"
    _LANG_VER = "6.10.1"
    _CMDS_VER = "6.5.0"
    _AUTO_VER = "6.16.0"
    _SEARCH_VER = "6.5.6"
    _LINT_VER = "6.8.1"
    _PY_VER = "6.1.6"
    _JS_VER = "6.2.2"
    _THEME_VER = "6.1.2"
    
    # Core Maps
    import_map = {
        # CodeMirror Packages
        "@codemirror/state": f"https://unpkg.com/@codemirror/state@{_STATE_VER}/dist/index.js",
        "@codemirror/view": f"https://unpkg.com/@codemirror/view@{_VIEW_VER}/dist/index.js",
        "@codemirror/language": f"https://unpkg.com/@codemirror/language@{_LANG_VER}/dist/index.js",
        "@codemirror/commands": f"https://unpkg.com/@codemirror/commands@{_CMDS_VER}/dist/index.js",
        "@codemirror/autocomplete": f"https://unpkg.com/@codemirror/autocomplete@{_AUTO_VER}/dist/index.js",
        "@codemirror/search": f"https://unpkg.com/@codemirror/search@{_SEARCH_VER}/dist/index.js",
        "@codemirror/lint": f"https://unpkg.com/@codemirror/lint@{_LINT_VER}/dist/index.js",
        
        # Languages & Themes
        "@codemirror/lang-python": f"https://unpkg.com/@codemirror/lang-python@{_PY_VER}/dist/index.js",
        "@codemirror/lang-javascript": f"https://unpkg.com/@codemirror/lang-javascript@{_JS_VER}/dist/index.js",
        "@codemirror/theme-one-dark": f"https://unpkg.com/@codemirror/theme-one-dark@{_THEME_VER}/dist/index.js",
        
        # Transitive Dependencies (Must map these or it fails!)
        "style-mod": "https://unpkg.com/style-mod@4.1.0/src/style-mod.js",
        "w3c-keyname": "https://unpkg.com/w3c-keyname@2.2.8/index.js",
        "@lezer/common": "https://unpkg.com/@lezer/common@1.2.1/dist/index.js",
        "@lezer/highlight": "https://unpkg.com/@lezer/highlight@1.2.0/dist/index.js",
        "@lezer/lr": "https://unpkg.com/@lezer/lr@1.4.0/dist/index.js",
        "@lezer/python": "https://unpkg.com/@lezer/python@1.1.14/dist/index.js",
        "@lezer/javascript": "https://unpkg.com/@lezer/javascript@1.4.14/dist/index.js",
        "crelt": "https://unpkg.com/crelt@1.0.6/index.js"
    }
    
    # Imports use bare specifiers (resolved by map)
    imports = {
        "state": "@codemirror/state",
        "view": "@codemirror/view",
        "language": "@codemirror/language",  # For syntax highlighting
        "commands": "@codemirror/commands",
        "python": "@codemirror/lang-python",
        "javascript": "@codemirror/lang-javascript",
        "one_dark": "@codemirror/theme-one-dark"
    }

    def render(self):
        value = ComponentSignal("value", "")      # -> $$value in JS
        theme = ComponentSignal("theme", "light") # -> $$theme in JS
        lang = ComponentSignal("lang", "python")  # -> $$lang in JS

        return Div(
            value, theme, lang,
            Div(
                data_ref="editor",
                style="border: 1px solid #ccc; border-radius: 4px; overflow: hidden; height: 100%; text-align: left;",
            ),
            data_on_theme_change=("$$theme = evt.detail.value", {"trusted": True}),
            data_on_lang_change=("$$lang = evt.detail.value", {"trusted": True}),
            data_on_value_change=("$$value = evt.detail.value", {"trusted": True}),
            style="height: 100%;",  # Fill parent container
        )

    def setup(self):
        return """
            if (!state || !view || !commands || !language) {
                console.error('[CodeEditor] Failed to load dependencies');
                return;
            }

            const { EditorState, Compartment } = state;
            const { EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter, drawSelection } = view;
            const { defaultKeymap, history, historyKeymap } = commands;
            const { syntaxHighlighting, defaultHighlightStyle, HighlightStyle } = language;

            // Base extensions (theme-independent)
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

            // Theme includes both editor styling AND syntax highlighting
            const getTheme = (t) => {
                if (t === 'dark' && one_dark) {
                    // oneDark includes both theme and syntax highlighting
                    return one_dark.oneDark;
                }
                // Light theme: just use default syntax highlighting
                return syntaxHighlighting(defaultHighlightStyle);
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
                                const val = update.state.doc.toString();
                                el.dispatchEvent(new CustomEvent('change', {
                                    detail: { value: val },
                                    bubbles: true
                                }));
                            }
                        })
                    ]
                }),
                parent: refs('editor')
            });

            // Separate effects for theme/lang vs value to avoid unwanted resets

            // Effect 1: Theme and language switching (doesn't touch content)
            effect(() => {
                const currentTheme = $$theme;
                const currentLang = $$lang;

                view_inst.dispatch({
                    effects: [
                        themeConfig.reconfigure(getTheme(currentTheme)),
                        langConfig.reconfigure(getLang(currentLang))
                    ]
                });
            });

            // Effect 2: External value changes (only if value signal is explicitly set)
            // This is for programmatic updates, not user typing
            let lastExternalValue = initialDoc;
            effect(() => {
                const currentValue = $$value;
                // Only update if value changed externally (not from user typing)
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

            onCleanup(() => {
                view_inst.destroy();
            });
        """

app, rt = star_app()
app.register(CodeEditor)
app.devtools_json()

@rt("/")
def home():
    # Page-level signals for tracking editor output
    (current_code := Signal("current_code", "print('Hello, StarHTML!')"))
    (output := Signal("output", "Waiting for run..."))
    (editor_theme := Signal("editor_theme", "light"))
    (editor_lang := Signal("editor_lang", "python"))

    return Div(
        current_code, output, editor_theme, editor_lang,

        H1("StarElements CodeMirror Demo"),
        P("A Python-native web component wrapping CodeMirror 6."),

        # Controls - set page signals, component reacts via attribute binding
        # Note: data-class expects {className: boolean} object, not a string
        Div(
            Div(
                Button("Python",
                       data_on_click=editor_lang.set("python"),
                       cls="btn",
                       data_class_active=(editor_lang == "python")),
                Button("JavaScript",
                       data_on_click=editor_lang.set("javascript"),
                       cls="btn",
                       data_class_active=(editor_lang == "javascript")),
                style="display: flex; gap: 10px;",
            ),
            Button(
                data_text=(editor_theme == "light").if_("Switch to Dark", "Switch to Light"),
                data_on_click=(editor_theme == "light").if_(editor_theme.set("dark"), editor_theme.set("light")),
                cls="btn",
            ),
            style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;",
        ),

        CodeEditor(
            value="print('Hello, StarHTML!')",
            # Bind attributes to page signals - component reacts via attributeChangedCallback
            data_attr_theme=editor_theme,
            data_attr_lang=editor_lang,
            data_on_change=current_code.set(evt.detail.value),
            style="height: 300px;",
        ),

        Div(
            Button(
                "Run Code",
                data_on_click=output.set("Executing...\n\n" + current_code),
                cls="btn run-btn"
            ),
            style="margin-top: 10px; text-align: right;"
        ),

        Div(
            H1("Output", style="margin-top: 20px; font-size: 1.5em;"),
            Pre(data_text=output, style="padding: 20px; background: #222; color: #0f0; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; font-family: monospace; min-height: 50px;"),
            style="margin-top: 20px;"
        ),

        Style("""
            .btn {
                padding: 8px 16px;
                border: 1px solid #ccc;
                background: white;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            .btn:hover { background: #f0f0f0; }
            .btn.active {
                background: #007bff;
                color: white;
                border-color: #007bff;
            }
            .run-btn {
                background: #28a745;
                color: white;
                border-color: #28a745;
                font-weight: bold;
            }
            .run-btn:hover { background: #218838; }
        """),

        style="max-width: 900px; margin: 0 auto; padding: 40px; font-family: sans-serif;",
        cls="demo-container"
    )

if __name__ == "__main__":
    from starhtml import serve
    print("Starting CodeMirror Demo...")
    serve(port=8000)