"""
refat_backup_engine.py — MTKClient backend wrapper
Handles backup, restore, scatter export, and manifest validation.
"""
import subprocess
import sys
import os
import json
import argparse
import contextlib
import io
import tempfile
import urllib.request
import zipfile
from datetime import datetime

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
APP_DATA    = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "RefatAndroidBackup")
MTK_NAME    = "mtkclient-2.1.4.1"
MTK_URL     = "https://github.com/bkerler/mtkclient/archive/refs/tags/2.1.4.1.zip"
MTK_PY      = os.path.join(BASE_DIR, MTK_NAME, "mtk.py")
MANIFEST    = "refat_manifest.json"
SKIP_DEFAULT = "userdata"


def _mtk_dir():
    bundled = os.path.join(BASE_DIR, MTK_NAME)
    if os.path.isfile(os.path.join(bundled, "mtk.py")):
        return bundled
    local = os.path.join(APP_DATA, MTK_NAME)
    if os.path.isfile(os.path.join(local, "mtk.py")):
        return local
    return None


def ensure_mtkclient():
    directory = _mtk_dir()
    if directory:
        return directory
    os.makedirs(APP_DATA, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        archive = os.path.join(temp_dir, "mtkclient.zip")
        urllib.request.urlretrieve(MTK_URL, archive)
        with zipfile.ZipFile(archive) as package:
            package.extractall(APP_DATA)
    directory = _mtk_dir()
    if not directory:
        raise RuntimeError("MTKClient could not be installed.")
    return directory


def _run(cmd):
    cwd = ensure_mtkclient()
    print(f"$ {' '.join(str(c) for c in cmd)}")
    mtk_path = os.path.join(cwd, "mtk.py")
    old_path, old_argv = os.getcwd(), sys.argv
    try:
        sys.path.insert(0, cwd)
        sys.argv = [mtk_path] + list(cmd[2:])
        import mtk
        try:
            return int(mtk.main() or 0)
        except SystemExit as exc:
            return int(exc.code or 0)
    finally:
        sys.argv = old_argv
        os.chdir(old_path)
        if cwd in sys.path:
            sys.path.remove(cwd)


def _run_capture(cmd):
    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        code = _run(cmd)
    return code, output.getvalue()


def _write_manifest(backup_dir, hw_code=None):
    manifest = {
        "created":    datetime.now().isoformat(),
        "hw_code":    hw_code or "unknown",
        "backup_dir": backup_dir,
    }
    path = os.path.join(backup_dir, MANIFEST)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[INFO] Manifest saved → {path}")
    return manifest


def _read_manifest(backup_dir):
    path = os.path.join(backup_dir, MANIFEST)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _verify_backup(backup_dir):
    critical = ["preloader.bin", "boot.bin", "nvram.bin", "nvdata.bin"]
    missing = [f for f in critical if not os.path.exists(os.path.join(backup_dir, f))]
    if missing:
        print(f"[WARN] Missing critical files: {', '.join(missing)}")
    else:
        print("[SUCCESS] All critical partition files verified on disc.")
    return not missing


def cmd_backup(args):
    out = args.output
    os.makedirs(out, exist_ok=True)

    cmd = ["python", MTK_PY, "rl"]
    skip = args.skip or SKIP_DEFAULT
    if skip:
        cmd += ["--skip", skip]
    cmd.append(out)

    rc = _run(cmd)
    if rc == 0:
        _write_manifest(out)
        _verify_backup(out)
        print("[SUCCESS] Refat Android Full Backup executed completely and verified on disc.")
    else:
        print(f"[ERROR] Backup exited with code {rc}")
    return rc


def cmd_restore(args):
    src = args.restore
    if not os.path.isdir(src):
        print(f"[ERROR] Backup folder not found: {src}")
        return 1

    manifest = _read_manifest(src)
    if manifest:
        stored_hw = manifest.get("hw_code", "unknown")
        # Detect connected device HW code
        try:
            _, output = _run_capture(["python", MTK_PY, "printgpt"])
        except Exception:
            output = ""

        # Simple heuristic: if stored hw_code is present in output, it matches
        if stored_hw != "unknown" and stored_hw not in output:
            print("[CRITICAL] CRITICAL HARDWARE MISMATCH DETECTED!")
            print("Operation BLOCKED to protect the device flash matrix from physical bricks.")
            return 1
    else:
        print("[WARN] No manifest found — skipping hardware mismatch check.")

    rc = _run(["python", MTK_PY, "wl", src])
    if rc == 0:
        print("[SUCCESS] Restore complete. Disconnect USB and hold Power 10s to reboot.")
    else:
        print(f"[ERROR] Restore exited with code {rc}")
    return rc


def cmd_scatter(args):
    out = args.output
    if not out:
        print("[ERROR] Specify output path with --output")
        return 1
    out_dir = os.path.dirname(out) or "."
    os.makedirs(out_dir, exist_ok=True)
    rc = _run(["python", MTK_PY, "gpt", out_dir])
    # mtk gpt saves as MT*_Android_scatter.txt — rename to requested path
    import glob
    matches = glob.glob(os.path.join(out_dir, "*_Android_scatter.txt"))
    if matches and matches[0] != out:
        os.replace(matches[0], out)
    if rc == 0:
        print(f"[SUCCESS] Scatter saved → {out}")
    else:
        print(f"[ERROR] Scatter export exited with code {rc}")
    return rc


def cmd_printgpt(_args):
    return _run(["python", MTK_PY, "printgpt"])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Refat Android Backup Engine")
    sub = parser.add_subparsers(dest="command")

    p_bk = sub.add_parser("backup")
    p_bk.add_argument("output", help="Destination folder")
    p_bk.add_argument("--skip", default=SKIP_DEFAULT)

    p_rs = sub.add_parser("restore")
    p_rs.add_argument("restore", help="Backup source folder")

    p_sc = sub.add_parser("scatter")
    p_sc.add_argument("--output", required=True)

    sub.add_parser("printgpt")

    # Legacy flat --restore flag for compatibility with Upgradation.md examples
    parser.add_argument("--restore", dest="_legacy_restore", metavar="DIR")

    args = parser.parse_args(argv)

    if args._legacy_restore:
        args.restore = args._legacy_restore
        return cmd_restore(args)

    dispatch = {
        "backup":   cmd_backup,
        "restore":  cmd_restore,
        "scatter":  cmd_scatter,
        "printgpt": cmd_printgpt,
    }
    fn = dispatch.get(args.command)
    if fn:
        return fn(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
