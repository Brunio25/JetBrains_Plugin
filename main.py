import re
from dataclasses import dataclass
from pathlib import Path
from sys import platform
from typing import Union
from xml.etree import ElementTree

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.event import KeywordQueryEvent, PreferencesEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem


@dataclass
class Project:
    name: str
    path: str
    last_opened: int


@dataclass
class Editor:
    name: str
    icon: Path
    config_dir_prefix: str
    binary: str

    def __init__(self, name: str, icon: Path, config_dir_prefix: str, binaries_path: str, binaries: list[str]):
        self.name = name
        self.icon = icon
        self.config_dir_prefix = config_dir_prefix
        self.binary = self._find_binary(binaries_path, binaries)

    @staticmethod
    def _find_binary(binaries_path: str, binaries: list[str]) -> Union[str, None]:
        for binary in binaries:
            if Path(f"{binaries_path}/{binary}").expanduser().is_file():
                return Path(f"{binaries_path}/{binary}").expanduser().__str__()
        return None

    def list_projects(self) -> list[Project]:
        config_dir = Path.home() / ".config"
        if platform == "darwin":
            config_dir = Path.home() / "Library" / "Application Support"

        dirs = list(config_dir.glob(f"{self.config_dir_prefix}*/"))
        if not dirs:
            return []
        latest = sorted(dirs)[-1]
        return self._parse_recent_projects(Path(latest) / "options" / "recentProjects.xml")

    @staticmethod
    def _parse_recent_projects(recent_projects_file: Path) -> list[Project]:
        try:
            root = ElementTree.parse(recent_projects_file).getroot()
            entries = root.findall(".//component[@name='RecentProjectsManager']//entry[@key]")

            projects = []
            for entry in entries:
                project_path = entry.attrib["key"].replace("$USER_HOME$", str(Path.home()))

                tag_opened = entry.find(".//option[@name='projectOpenTimestamp']")
                last_opened = tag_opened.attrib["value"] \
                    if tag_opened is not None and "value" in tag_opened.attrib else None

                if project_path and last_opened:
                    projects.append(
                        Project(name=Path(project_path).name, path=project_path, last_opened=int(last_opened))
                    )
            return projects
        except (ElementTree.ParseError, FileNotFoundError):
            return []


class JetBrainsExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(PreferencesEvent, PreferencesEventListener())


class KeywordQueryEventListener(EventListener):
    def __init__(self, preferences):
        super().__init__()
        self.preferences = preferences
        plugin_dir = Path(__file__).parent
        binaries_path = preferences['binaries']
        editors = [
            Editor(
                name="Android Studio",
                icon=plugin_dir / "images" / "androidstudio.svg",
                config_dir_prefix="Google/AndroidStudio",
                binaries_path=binaries_path,
                binaries=["studio", "androidstudio", "android-studio", "android-studio-canary", "jdk-android-studio",
                          "android-studio-system-jdk"]),
            Editor(
                name="CLion",
                icon=plugin_dir / "images" / "clion.svg",
                config_dir_prefix="JetBrains/CLion",
                binaries_path=binaries_path,
                binaries=["clion", "clion-eap"]),
            Editor(
                name="DataGrip",
                icon=plugin_dir / "images" / "datagrip.svg",
                config_dir_prefix="JetBrains/DataGrip",
                binaries_path=binaries_path,
                binaries=["datagrip", "datagrip-eap"]),
            Editor(
                name="DataSpell",
                icon=plugin_dir / "images" / "dataspell.svg",
                config_dir_prefix="JetBrains/DataSpell",
                binaries_path=binaries_path,
                binaries=["dataspell", "dataspell-eap"]),
            Editor(
                name="GoLand",
                icon=plugin_dir / "images" / "goland.svg",
                config_dir_prefix="JetBrains/GoLand",
                binaries_path=binaries_path,
                binaries=["goland", "goland-eap"]),
            Editor(
                name="IntelliJ IDEA",
                icon=plugin_dir / "images" / "idea.svg",
                config_dir_prefix="JetBrains/IntelliJIdea",
                binaries_path=binaries_path,
                binaries=["idea", "idea.sh", "idea-ultimate", "idea-ce-eap", "idea-ue-eap", "intellij-idea-ce",
                          "intellij-idea-ce-eap", "intellij-idea-ue-bundled-jre", "intellij-idea-ultimate-edition",
                          "intellij-idea-community-edition-jre", "intellij-idea-community-edition-no-jre"]),
            Editor(
                name="PhpStorm",
                icon=plugin_dir / "images" / "phpstorm.svg",
                config_dir_prefix="JetBrains/PhpStorm",
                binaries_path=binaries_path,
                binaries=["phpstorm", "phpstorm-eap"]),
            Editor(
                name="PyCharm",
                icon=plugin_dir / "images" / "pycharm.svg",
                config_dir_prefix="JetBrains/PyCharm",
                binaries_path=binaries_path,
                binaries=["charm", "pycharm", "pycharm-eap"]),
            Editor(
                name="Rider",
                icon=plugin_dir / "images" / "rider.svg",
                config_dir_prefix="JetBrains/Rider",
                binaries_path=binaries_path,
                binaries=["rider", "rider-eap"]),
            Editor(
                name="RubyMine",
                icon=plugin_dir / "images" / "rubymine.svg",
                config_dir_prefix="JetBrains/RubyMine",
                binaries_path=binaries_path,
                binaries=["rubymine", "rubymine-eap", "jetbrains-rubymine", "jetbrains-rubymine-eap"]),
            Editor(
                name="WebStorm",
                icon=plugin_dir / "images" / "webstorm.svg",
                config_dir_prefix="JetBrains/WebStorm",
                binaries_path=binaries_path,
                binaries=["webstorm", "webstorm-eap"]),
            Editor(
                name="RustRover",
                icon=plugin_dir / "images" / "rustrover.svg",
                config_dir_prefix="JetBrains/RustRover",
                binaries_path=binaries_path,
                binaries=["rustrover", "rustrover-eap"]),
        ]
        self.editors = [editor for editor in editors if editor.binary is not None]

    def on_event(self, event: KeywordQueryEvent, extension: JetBrainsExtension):
        query = event.get_query().get_argument(default="")

        editor_project_pairs = []
        for editor in self.editors:
            projects = editor.list_projects()
            projects = [project for project in projects if Path(project.path).exists()]
            projects = [project for project in projects if re.search(query, project.name, re.IGNORECASE)]
            editor_project_pairs.extend([(editor, p) for p in projects])

        editor_project_pairs.sort(key=lambda pair: pair[1].last_opened, reverse=True)
        editor_project_pairs = editor_project_pairs[:int(self.preferences['item_limit'])]

        return RenderResultListAction([
            ExtensionResultItem(
                name=project.name,
                description=project.path,
                icon=editor.icon.__str__(),
                on_enter=RunScriptAction(f"{editor.binary} {project.path}")
            )
            for editor, project in editor_project_pairs
        ])


class PreferencesEventListener(EventListener):
    def on_event(self, event: PreferencesEvent, extension: JetBrainsExtension):
        extension.subscribe(KeywordQueryEvent, KeywordQueryEventListener(event.preferences))


if __name__ == '__main__':
    JetBrainsExtension().run()
