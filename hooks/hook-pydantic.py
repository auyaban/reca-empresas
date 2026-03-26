from PyInstaller.utils.hooks import collect_submodules


_EXCLUDED_PREFIXES = (
    "pydantic.v1",
    "pydantic.mypy",
    "pydantic._hypothesis_plugin",
)


def _include(module_name):
    return not any(
        module_name == prefix or module_name.startswith(prefix + ".")
        for prefix in _EXCLUDED_PREFIXES
    )


hiddenimports = collect_submodules("pydantic", filter=_include, on_error="warn once")

excludedimports = [
    "pydantic.v1",
    "pydantic.mypy",
    "pydantic._hypothesis_plugin",
]
