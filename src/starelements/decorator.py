from pathlib import Path

from .core import ElementDef

_element_registry: dict[str, type] = {}


def get_registered_elements() -> list[type]:
    return list(_element_registry.values())


def clear_registry():
    _element_registry.clear()


def element(
    name: str,
    *,
    package: str | None = None,
    static_path: str | Path | None = None,
    shadow: bool = False,
    form_associated: bool = False,
    height: str | None = None,
    width: str = "100%",
    dimensions: dict[str, str] | None = None,
    skeleton: bool | None = None,
    imports: dict[str, str] | None = None,
    import_map: dict[str, str] | None = None,
    scripts: dict[str, str] | None = None,
    events: list[str] | None = None,
    signals: dict[str, tuple] | None = None,
    methods: tuple[str, ...] | None = None,
):
    if dimensions:
        normalized_dims = {k.replace("_", "-"): v for k, v in dimensions.items()}
    else:
        normalized_dims = {"width": width}
        if height:
            normalized_dims["min-height"] = height

    use_skeleton = skeleton if skeleton is not None else "min-height" in normalized_dims

    pkg_name = package or "starelements"
    pkg_static = Path(static_path) if static_path else None

    def decorator(fn):
        from .core import ElementInstance
        from .integration import get_static_path as _get_se_static

        resolved_static = pkg_static or _get_se_static()

        elem_def = ElementDef(
            tag_name=name,
            imports=imports or {},
            import_map=import_map or {},
            scripts=scripts or {},
            events=events or [],
            render_fn=fn,
            shadow=shadow,
            form_associated=form_associated,
            dimensions=normalized_dims,
            skeleton=use_skeleton,
            static_path=resolved_static,
            signals=signals or {},
            methods=methods or (),
        )

        class ElementFactory:
            _element_def = elem_def
            _package_name = pkg_name
            _static_path = resolved_static

            def __new__(cls_inner, **kwargs):
                return ElementInstance(elem_def, **kwargs)

            @classmethod
            def get_package_name(cls) -> str:
                return cls._package_name

            @classmethod
            def get_static_path(cls):
                return cls._static_path

            @classmethod
            def get_headers(cls, pkg_prefix: str) -> tuple:
                from .integration import _starelements_hdrs

                return _starelements_hdrs(cls, pkg_prefix=pkg_prefix)

            @classmethod
            def get_import_map(cls, pkg_prefix: str) -> dict[str, str]:
                return {
                    **elem_def.import_map,
                    **{
                        alias: spec
                        for alias, spec in elem_def.imports.items()
                        if spec.startswith(("http://", "https://", "/"))
                    },
                }

            @classmethod
            def get_dependencies(cls) -> list[tuple[str, Path]]:
                from .integration import get_static_path as _get_se_static

                return [("starelements", _get_se_static())]

        ElementFactory.__name__ = fn.__name__
        ElementFactory.__doc__ = fn.__doc__
        ElementFactory.__module__ = fn.__module__

        _element_registry[name] = ElementFactory
        return ElementFactory

    return decorator
