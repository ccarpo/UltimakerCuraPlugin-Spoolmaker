import os

from UM.Extension import Extension
from UM.Logger import Logger
from UM.Message import Message
from UM.Resources import Resources

from .MaterialWriter import MaterialWriter
from .SpoolmanClient import SpoolmanClient, SpoolmanError

try:
    from cura.CuraApplication import CuraApplication
except ImportError:
    CuraApplication = None


class SpoolmanMaterialExtension(Extension):
    def __init__(self) -> None:
        super().__init__()
        self._client = SpoolmanClient()
        self.setMenuName("Spoolman")
        self.addMenuItem("Import materials from Spoolman", self.importMaterials)

    def importMaterials(self) -> None:
        try:
            material_directory = self._get_material_directory()
            spools = self._client.fetch_spools(allow_archived=False)
            writer = MaterialWriter(self._client.base_url)
            filaments, skipped = writer.collect_filaments(spools)

            if not filaments:
                self._show_message(
                    "Spoolman import",
                    "No usable filament definitions were found in Spoolman.",
                    Message.MessageType.WARNING,
                    lifetime=8,
                )
                return

            result = writer.write_materials(material_directory, filaments, skipped=skipped)
            restart_note = "Restart Cura if the new materials do not appear immediately."
            summary = (
                f"Imported: {result.imported}\n"
                f"Updated: {result.updated}\n"
                f"Removed: {result.deleted}\n"
                f"Skipped: {result.skipped}\n"
                f"Failed: {result.failed}\n"
                f"Location: {result.output_directory}\n\n"
                f"{restart_note}"
            )
            message_type = Message.MessageType.POSITIVE if result.failed == 0 else Message.MessageType.WARNING
            self._show_message("Spoolman import complete", summary, message_type, lifetime=0)
            Logger.log("i", f"Spoolman material import completed: {summary}")
        except SpoolmanError as error:
            Logger.log("e", f"Spoolman import failed: {error}")
            self._show_message("Spoolman import failed", str(error), Message.MessageType.ERROR, lifetime=0)
        except Exception:
            Logger.logException("e", "Unexpected error while importing Spoolman materials.")
            self._show_message(
                "Spoolman import failed",
                "Unexpected error while importing materials from Spoolman. Check cura.log for details.",
                Message.MessageType.ERROR,
                lifetime=0,
            )

    def _get_material_directory(self) -> str:
        candidate_roots = []

        if CuraApplication is not None:
            resource_types = getattr(CuraApplication, "ResourceTypes", None)
            material_type = getattr(resource_types, "MaterialInstanceContainer", None) if resource_types else None
            if material_type is not None:
                try:
                    candidate_roots.append(Resources.getStoragePathForType(material_type))
                except Exception:
                    pass
                try:
                    candidate_roots.append(Resources.getStoragePath(material_type))
                except Exception:
                    pass

        try:
            data_storage = Resources.getDataStoragePath()
            if data_storage:
                candidate_roots.append(os.path.join(data_storage, "materials"))
        except Exception:
            pass

        for candidate_root in candidate_roots:
            if candidate_root:
                target_directory = os.path.join(candidate_root, "spoolman")
                os.makedirs(target_directory, exist_ok=True)
                return target_directory

        raise RuntimeError("Unable to determine Cura material storage directory.")

    def _show_message(self, title: str, text: str, message_type: Message.MessageType, lifetime: int) -> None:
        Message(text=text, title=title, lifetime=lifetime, message_type=message_type).show()
