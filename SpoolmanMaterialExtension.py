import os

from PyQt6.QtWidgets import QInputDialog, QLineEdit

from UM.Application import Application
from UM.Extension import Extension
from UM.Logger import Logger
from UM.Message import Message
from UM.Resources import Resources

from .MaterialWriter import CollectionResult, MaterialWriter
from .SpoolmanClient import SpoolmanClient, SpoolmanError

try:
    from cura.CuraApplication import CuraApplication
except ImportError:
    CuraApplication = None


class SpoolmanMaterialExtension(Extension):
    _BASE_URL_PREFERENCE_KEY = "spoolman_materials/base_url"

    def __init__(self) -> None:
        super().__init__()
        self._application = Application.getInstance()
        self._preferences = self._application.getPreferences()
        self._preferences.addPreference(self._BASE_URL_PREFERENCE_KEY, SpoolmanClient.DEFAULT_BASE_URL)
        try:
            configured_base_url = self._get_configured_base_url()
        except SpoolmanError:
            configured_base_url = SpoolmanClient.DEFAULT_BASE_URL
            self._preferences.setValue(self._BASE_URL_PREFERENCE_KEY, configured_base_url)
        self._client = SpoolmanClient(configured_base_url)
        self.setMenuName("Spoolman")
        self.addMenuItem("Configure Spoolman URL", self.configureBaseUrl)
        self.addMenuItem("Test Spoolman connection", self.testConnection)
        self.addMenuItem("Preview import from Spoolman", self.previewImport)
        self.addMenuItem("Import materials from Spoolman", self.importMaterials)

    def configureBaseUrl(self) -> None:
        current_value = self._preferences.getValue(self._BASE_URL_PREFERENCE_KEY) or self._client.base_url
        new_value, accepted = QInputDialog.getText(
            None,
            "Configure Spoolman URL",
            "Spoolman base URL:",
            QLineEdit.EchoMode.Normal,
            str(current_value),
        )
        if not accepted:
            return

        try:
            normalized_url = SpoolmanClient.normalize_base_url(new_value)
            self._preferences.setValue(self._BASE_URL_PREFERENCE_KEY, normalized_url)
            self._client.set_base_url(normalized_url)
        except SpoolmanError as error:
            self._show_message("Spoolman configuration", str(error), Message.MessageType.ERROR, lifetime=0)
            return

        self._show_message(
            "Spoolman configuration saved",
            f"Configured Spoolman URL: {normalized_url}",
            Message.MessageType.POSITIVE,
            lifetime=8,
        )

    def testConnection(self) -> None:
        try:
            self._client.set_base_url(self._get_configured_base_url())
            result = self._client.test_connection()
            summary = (
                f"Configured URL: {result['base_url']}\n"
                f"Spools returned: {result['spool_count']}"
            )
            self._show_message("Spoolman connection successful", summary, Message.MessageType.POSITIVE, lifetime=8)
        except SpoolmanError as error:
            Logger.log("e", f"Spoolman connection test failed: {error}")
            self._show_message("Spoolman connection failed", str(error), Message.MessageType.ERROR, lifetime=0)

    def previewImport(self) -> None:
        try:
            collection = self._collect_filaments()
            summary = self._format_collection_summary(self._client.base_url, collection)
            message_type = Message.MessageType.POSITIVE if collection.unique_filament_count > 0 else Message.MessageType.WARNING
            self._show_message("Spoolman import preview", summary, message_type, lifetime=0)
        except SpoolmanError as error:
            Logger.log("e", f"Spoolman preview failed: {error}")
            self._show_message("Spoolman preview failed", str(error), Message.MessageType.ERROR, lifetime=0)

    def importMaterials(self) -> None:
        try:
            material_directory = self._get_material_directory()
            collection = self._collect_filaments()

            if not collection.filaments:
                self._show_message(
                    "Spoolman import",
                    self._format_collection_summary(self._client.base_url, collection),
                    Message.MessageType.WARNING,
                    lifetime=0,
                )
                return

            writer = MaterialWriter(self._client.base_url)
            result = writer.write_materials(material_directory, collection.filaments, skipped=collection.skipped)
            reload_succeeded = self._reload_materials()
            reload_note = self._build_reload_note(reload_succeeded, result.updated > 0)
            summary = (
                f"{self._format_collection_summary(self._client.base_url, collection)}\n\n"
                f"Imported: {result.imported}\n"
                f"Updated: {result.updated}\n"
                f"Removed: {result.deleted}\n"
                f"Skipped: {result.skipped}\n"
                f"Failed: {result.failed}\n"
                f"Location: {result.output_directory}\n\n"
                f"{reload_note}"
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

    def _collect_filaments(self) -> CollectionResult:
        self._client.set_base_url(self._get_configured_base_url())
        spools = self._client.fetch_spools(allow_archived=False)
        writer = MaterialWriter(self._client.base_url)
        return writer.collect_filaments(spools)

    def _get_configured_base_url(self) -> str:
        configured_value = self._preferences.getValue(self._BASE_URL_PREFERENCE_KEY)
        if not configured_value:
            configured_value = SpoolmanClient.DEFAULT_BASE_URL
        return SpoolmanClient.normalize_base_url(str(configured_value))

    def _format_collection_summary(self, base_url: str, collection: CollectionResult) -> str:
        return (
            f"Configured URL: {base_url}\n"
            f"Spools returned: {collection.total_spools}\n"
            f"Distinct filament definitions: {collection.unique_filament_count}\n"
            f"Archived ignored: {collection.archived_spools}\n"
            f"Duplicate filament spools: {collection.duplicate_filament_spools}\n"
            f"Skipped malformed: {collection.skipped}"
        )

    def _reload_materials(self) -> bool:
        if CuraApplication is None:
            return False

        try:
            registry = CuraApplication.getInstance().getContainerRegistry()
        except Exception:
            return False

        try:
            registry.loadAllMetadata()
            registry.load()
            return True
        except Exception:
            Logger.logException("w", "Best-effort Cura material reload failed after Spoolman import.")
            return False

    def _build_reload_note(self, reload_succeeded: bool, has_updates: bool) -> str:
        if reload_succeeded and has_updates:
            return "Best-effort material reload was triggered, but Cura may still need a restart to reflect updates to existing materials."
        if reload_succeeded:
            return "Best-effort material reload was triggered. If the new materials do not appear immediately, restart Cura."
        return "Restart Cura if the new materials do not appear immediately."

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
