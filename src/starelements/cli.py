"""starelements CLI."""

import sys
from datetime import datetime
from pathlib import Path

import httpx

from .bundler import (
    ESBUILD_VERSION,
    ensure_esbuild,
    bundle_package,
    resolve_version,
    load_config,
    read_lock_file,
    write_lock_file,
    LockFile,
    LockedPackage,
    compute_integrity,
)


def cmd_bundle(project_root: Path | None = None) -> int:
    """Bundle JavaScript dependencies.

    Args:
        project_root: Project directory (defaults to cwd)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if project_root is None:
        project_root = Path.cwd()

    config = load_config(project_root)
    if not config:
        print("No [tool.starelements] bundle config found in pyproject.toml")
        return 1

    lock_path = project_root / "starelements.lock"
    lock = read_lock_file(lock_path)
    lock.esbuild_version = ESBUILD_VERSION

    try:
        # Ensure esbuild is available
        ensure_esbuild()

        # Create output directory
        config.output.mkdir(parents=True, exist_ok=True)

        for pkg_spec in config.packages:
            # Handle scoped packages (@org/name) vs version specifier
            if pkg_spec.startswith("@"):
                # Scoped package - find @ after the first /
                slash_idx = pkg_spec.find("/")
                if slash_idx != -1:
                    at_idx = pkg_spec.find("@", slash_idx)
                    if at_idx != -1:
                        name, version = pkg_spec[:at_idx], pkg_spec[at_idx + 1 :]
                    else:
                        name, version = pkg_spec, "latest"
                else:
                    # Invalid scoped package, treat as-is
                    name, version = pkg_spec, "latest"
            elif "@" in pkg_spec:
                name, version = pkg_spec.rsplit("@", 1)
            else:
                name, version = pkg_spec, "latest"

            # Resolve to exact version
            exact_version = resolve_version(name, version)

            # Generate output filename
            output_name = name.replace("/", "__").replace(".", "_") + ".bundle.js"
            output_path = config.output / output_name

            print(f"Bundling {name}@{exact_version}...")
            bundle_package(name, exact_version, output_path, minify=config.minify)

            # Update lock file
            lock.packages[name] = LockedPackage(
                name=name,
                version=exact_version,
                integrity=compute_integrity(output_path),
                source_url=f"https://unpkg.com/{name}@{exact_version}",
                bundled_at=datetime.now().isoformat(),
            )
            print(f"  → {output_path}")

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
    """CLI entry point."""
    args = sys.argv[1:]

    if not args or args[0] == "bundle":
        sys.exit(cmd_bundle())
    elif args[0] == "clean":
        # Future: clean cached binaries
        print("Error: 'clean' command not implemented yet")
        sys.exit(1)
    else:
        print(f"Unknown command: {args[0]}")
        print("Usage: starelements bundle")
        sys.exit(1)


if __name__ == "__main__":
    main()
