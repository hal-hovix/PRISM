
import importlib
import pkgutil
from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class Plugin:
    name: str
    version: str
    module: Any
    capabilities: List[str]
    labels: List[str]


def discover_plugins() -> Dict[str, Plugin]:
    discovered: Dict[str, Plugin] = {}
    package_name = "src.api.plugins"
    package = importlib.import_module(package_name)
    for _, mod_name, is_pkg in pkgutil.iter_modules(package.__path__):
        if is_pkg:
            continue
        module = importlib.import_module(f"{package_name}.{mod_name}")
        if hasattr(module, "register"):
            meta = module.register()
            plugin = Plugin(
                name=meta.get("name", mod_name),
                version=meta.get("version", "v0.0.0"),
                module=module,
                capabilities=meta.get("capabilities", []),
                labels=meta.get("labels", []),
            )
            discovered[plugin.name] = plugin
    return discovered


def classify_with_plugins(item: dict, *, llm, notion, config) -> dict:
    plugins = discover_plugins()
    best = {"type": "Note", "score": 0.0, "tags": [], "reason": "default"}
    for plugin in plugins.values():
        if "classify" not in plugin.capabilities:
            continue
        result = plugin.module.classify(item, llm=llm, notion=notion, config=config)
        if result and result.get("score", 0.0) > best.get("score", 0.0):
            best = result
    return best


