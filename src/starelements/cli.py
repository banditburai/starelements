import sys
from datetime import datetime
from pathlib import Path

import httpx

from .bundler import (
    BUNDLES_DIR,
    ESBUILD_VERSION,
    LockedPackage,
    bundle_filename,
    bundle_package,
    compute_integrity,
    ensure_esbuild,
    load_config,
    read_lock_file,
    resolve_version,
    write_lock_file,
)


def parse_package_spec(pkg_spec: str) -> tuple[str, str, str | None]:
    """Parse package specification into (name, version, entry_point).

    Formats:
    - "pkg" → (pkg, "latest", None)
    - "pkg@1.0" → (pkg, "1.0", None)
    - "pkg@1.0#entry.js" → (pkg, "1.0", "entry.js")
    - "@scope/pkg@1.0#entry.js" → (@scope/pkg, "1.0", "entry.js")
    """
    entry_point = None
    if "#" in pkg_spec:
        pkg_spec, entry_point = pkg_spec.rsplit("#", 1)

    if not pkg_spec.startswith("@"):
        if "@" in pkg_spec:
            name, version = pkg_spec.rsplit("@", 1)
        else:
            name, version = pkg_spec, "latest"
        return name, version, entry_point

    # Scoped packages: @ is both the scope prefix and version separator
    slash_idx = pkg_spec.find("/")
    if slash_idx == -1:
        return pkg_spec, "latest", entry_point

    at_idx = pkg_spec.find("@", slash_idx)
    if at_idx != -1:
        return pkg_spec[:at_idx], pkg_spec[at_idx + 1 :], entry_point
    return pkg_spec, "latest", entry_point


def cmd_bundle(project_root: Path | None = None) -> int:
    if project_root is None:
        project_root = Path.cwd()

    config = load_config(project_root)
    if not config:
        print("No [tool.starelements] bundle config found in pyproject.toml")
        return 1

    lock_path = project_root / "starelements.lock"
    lock = read_lock_file(lock_path)
    lock.esbuild_version = ESBUILD_VERSION

    output_dir = project_root / BUNDLES_DIR

    try:
        ensure_esbuild()
        output_dir.mkdir(parents=True, exist_ok=True)

        for pkg_spec in config.packages:
            name, version, entry_point = parse_package_spec(pkg_spec)
            exact_version = resolve_version(name, version)

            output_path = output_dir / bundle_filename(name)

            entry_info = f" (entry: {entry_point})" if entry_point else ""
            print(f"Bundling {name}@{exact_version}{entry_info}...")
            bundle_package(
                name,
                exact_version,
                output_path,
                minify=config.minify,
                entry_point=entry_point,
            )

            lock.packages[name] = LockedPackage(
                name=name,
                version=exact_version,
                integrity=compute_integrity(output_path),
                source_url=f"https://unpkg.com/{name}@{exact_version}",
                bundled_at=datetime.now().isoformat(),
            )
            print(f"  -> {output_path}")

        write_lock_file(lock, lock_path)
        print(f"Lock file updated: {lock_path}")
        return 0

    except httpx.HTTPStatusError as e:
        print(f"Error: Failed to fetch package: {e.response.status_code} {e.request.url}")
        return 1
    except httpx.RequestError as e:
        print(f"Error: Network request failed: {e}")
        return 1
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1
    except OSError as e:
        print(f"Error: File operation failed: {e}")
        return 1


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] == "bundle":
        sys.exit(cmd_bundle())
    else:
        print(f"Unknown command: {args[0]}")
        print("Usage: starelements bundle")
        sys.exit(1)


if __name__ == "__main__":
    main()
