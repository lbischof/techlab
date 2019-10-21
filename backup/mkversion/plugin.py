from typing import List

import mkdocs, pathlib, os, shutil, tempfile, atexit, subprocess, json
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files, File


def get_versions(temp_dir: pathlib.Path) -> List[str]:
    try:
        with open(temp_dir / "versions.json") as version_file:
            versions = json.load(version_file)
    except FileNotFoundError:
        print(
            "Didn't find a versions.json. Assuming this is the first versioned docs build."
        )
        versions = []
    return versions


def clone_docs_branch(branch: str, clone_dir: pathlib.Path) -> None:

    print(f"Cloning {branch} to {clone_dir}")
    subprocess.run(["git", "worktree", "add", str(clone_dir), f"origin/{branch}"])
    try:
        os.unlink(str(clone_dir / ".git"))
    except FileNotFoundError:
        pass  # The branch doesn't exist yet, so nothing to clone


class Plugin(BasePlugin):
    config_scheme = (
        (
            "containing_div",
            mkdocs.config.config_options.Type(
                mkdocs.utils.string_types, default="div.navbar-header"
            ),
        ),
        ("inject_js", mkdocs.config.config_options.Type(bool, default=False)),
        ("docs_version", mkdocs.config.config_options.Type(str, default="latest")),
        ("previous_docs_versions", mkdocs.config.config_options.Private()),
        ("working_dir", mkdocs.config.config_options.Private()),
    )

    def on_config(self, config):
        temp_dir = tempfile.TemporaryDirectory()
        atexit.register(temp_dir.cleanup)
        self.config["working_dir"] = pathlib.Path(temp_dir.name)
        clone_docs_branch(config["remote_branch"], self.config["working_dir"])
        version = os.getenv(self.config["docs_version"], self.config["docs_version"])
        self.config["docs_version"] = version
        self.config["previous_docs_versions"] = get_versions(self.config["working_dir"])
        if self.config["inject_js"]:
            config["extra_javascript"].append("version-select.js")
        if version != "latest":
            config["site_url"] = f"{config.get('site_url', '')}{version}/"
        return config

    def on_files(self, files, config):
        version = self.config["docs_version"]
        if self.config["inject_js"]:
            script_path = (
                config["site_dir"]
                if version == "latest"
                else os.path.join(config["site_dir"], version)
            )
            f = File("version-select.js", config["docs_dir"], script_path, False)
            f.abs_src_path = os.path.join(
                os.path.dirname(__file__), "version-select.js"
            )
            files._files.append(f)
        if version == "latest":
            return files
        for f in files:
            f.abs_dest_path = os.path.normpath(
                os.path.join(config["site_dir"], version, f.dest_path)
            )

        return files

    def on_pre_page(self, page, config, *args, **kwargs):
        page.meta["version"] = self.config["docs_version"]
        return page

    def on_page_markdown(self, markdown, page, config, *args, **kwargs):
        if self.config["inject_js"]:
            markdown = f'{markdown}<div id="docs-version" data-version="{self.config["docs_version"]}" data-anchor_div="{self.config["containing_div"]}" style="display: none;" />'
        return markdown

    def on_post_build(self, config):
        version = self.config["docs_version"]
        versions = self.config["previous_docs_versions"]
        site_path = pathlib.Path(config["site_dir"])
        temp_dir = self.config["working_dir"]

        if version != "latest":
            misplaced_files = [
                site_path / f for f in site_path.iterdir() if str(f) != version
            ]
            for f in misplaced_files:
                try:
                    shutil.move(
                        str(f.absolute()), str((site_path / version).absolute())
                    )
                except shutil.Error as e:
                    pass

        # If building latest, move version directories into site_dir
        # If building a version, move everything _except_ that versions subdir
        if version == "latest":
            print(f"Building latest, moving only subdirs to {site_path}.")
            for v in versions:
                if v != "latest":
                    try:
                        print(f"Moving {v}.")
                        shutil.move(str(temp_dir / v), str(site_path))
                    except shutil.Error as e:
                        pass  # Probably in serve mode
        else:
            print(
                f"Building a version, moving everything except any version subdir matching this version to {site_path}."
            )
            for f in temp_dir.iterdir():
                if str(f) != version:
                    try:
                        shutil.move(str(f), str(site_path))
                    except shutil.Error as e:
                        pass  # Probably in serve mode
        if version != "latest":
            versions = sorted(set(versions + [version, "latest"]))
            pathlib.Path(config["site_dir"]).mkdir(exist_ok=True)
            with open(pathlib.Path(config["site_dir"]) / "versions.json", "w") as fout:
                json.dump(versions, fout)
