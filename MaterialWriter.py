import os
import re
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


_MATERIAL_NS = "http://www.ultimaker.com/material"
_CURA_NS = "http://www.ultimaker.com/cura"

ET.register_namespace("", _MATERIAL_NS)
ET.register_namespace("cura", _CURA_NS)


@dataclass
class CollectionResult:
    filaments: List[Dict[str, Any]]
    total_spools: int
    archived_spools: int
    duplicate_filament_spools: int
    skipped: int

    @property
    def unique_filament_count(self) -> int:
        return len(self.filaments)


@dataclass
class WriteResult:
    imported: int
    updated: int
    deleted: int
    failed: int
    skipped: int
    output_directory: str


class MaterialWriter:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def collect_filaments(self, spools: List[Dict[str, Any]]) -> CollectionResult:
        filaments_by_id: Dict[str, Dict[str, Any]] = {}
        archived_spools = 0
        duplicate_filament_spools = 0
        skipped = 0

        for spool in spools:
            if not isinstance(spool, dict):
                skipped += 1
                continue

            if spool.get("archived"):
                archived_spools += 1
                continue

            filament = spool.get("filament")
            if not isinstance(filament, dict):
                skipped += 1
                continue

            filament_id = filament.get("id")
            if filament_id is None:
                skipped += 1
                continue

            normalized = self._normalize_filament(filament)
            if normalized is None:
                skipped += 1
                continue

            filament_key = str(filament_id)
            if filament_key not in filaments_by_id:
                filaments_by_id[filament_key] = normalized
            else:
                duplicate_filament_spools += 1

        sorted_filaments = sorted(
            filaments_by_id.values(),
            key=lambda item: (item["brand"].lower(), item["material"].lower(), item["display_name"].lower())
        )
        return CollectionResult(
            filaments=sorted_filaments,
            total_spools=len(spools),
            archived_spools=archived_spools,
            duplicate_filament_spools=duplicate_filament_spools,
            skipped=skipped,
        )

    def write_materials(self, output_directory: str, filaments: List[Dict[str, Any]], skipped: int = 0) -> WriteResult:
        os.makedirs(output_directory, exist_ok=True)

        expected_files = set()
        imported = 0
        updated = 0
        failed = 0

        for filament in filaments:
            file_name = filament["file_name"]
            expected_files.add(file_name)
            file_path = os.path.join(output_directory, file_name)
            existed = os.path.exists(file_path)

            try:
                xml_bytes = self._build_xml(filament)
                self._write_bytes(file_path, xml_bytes)
            except OSError:
                failed += 1
                continue

            if existed:
                updated += 1
            else:
                imported += 1

        deleted = 0
        for existing_name in os.listdir(output_directory):
            existing_path = os.path.join(output_directory, existing_name)
            if not os.path.isfile(existing_path):
                continue
            if not existing_name.endswith(".xml.fdm_material"):
                continue
            if existing_name in expected_files:
                continue
            try:
                os.remove(existing_path)
                deleted += 1
            except OSError:
                failed += 1

        return WriteResult(
            imported=imported,
            updated=updated,
            deleted=deleted,
            failed=failed,
            skipped=skipped,
            output_directory=output_directory,
        )

    def _normalize_filament(self, filament: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        filament_id = filament.get("id")
        density = self._to_float(filament.get("density"))
        diameter = self._to_float(filament.get("diameter"))
        if filament_id is None or density is None or diameter is None:
            return None

        vendor = filament.get("vendor") if isinstance(filament.get("vendor"), dict) else {}
        brand = self._clean_text(vendor.get("name"), fallback="Spoolman")
        material = self._clean_text(filament.get("material"), fallback="Unknown")
        display_name = self._clean_text(filament.get("name"), fallback=f"Filament {filament_id}")
        color_name = self._derive_color_name(filament, display_name)
        description = self._build_description(filament)
        color_code = self._normalize_color_code(filament.get("color_hex"), filament.get("multi_color_hexes"))
        weight = self._to_float(filament.get("weight"))
        print_temperature = self._to_int(filament.get("settings_extruder_temp"))
        bed_temperature = self._to_int(filament.get("settings_bed_temp"))
        standby_temperature = max(print_temperature - 30, 0) if print_temperature is not None else None
        version = 1
        file_stem = self._slugify(f"spoolman_{brand}_{material}_{display_name}_{filament_id}")
        guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self._base_url}/filament/{filament_id}"))

        return {
            "filament_id": str(filament_id),
            "brand": brand,
            "material": material,
            "display_name": display_name,
            "color_name": color_name,
            "guid": guid,
            "version": str(version),
            "color_code": color_code,
            "description": description,
            "density": self._format_number(density),
            "diameter": self._format_number(diameter),
            "weight": self._format_number(weight) if weight is not None else None,
            "print_temperature": str(print_temperature) if print_temperature is not None else None,
            "bed_temperature": str(bed_temperature) if bed_temperature is not None else None,
            "standby_temperature": str(standby_temperature) if standby_temperature is not None else None,
            "file_name": f"{file_stem}.xml.fdm_material",
        }

    def _build_xml(self, filament: Dict[str, Any]) -> bytes:
        root = ET.Element(self._tag("fdmmaterial"), {"version": "1.3"})
        metadata = ET.SubElement(root, self._tag("metadata"))
        name = ET.SubElement(metadata, self._tag("name"))
        ET.SubElement(name, self._tag("brand")).text = filament["brand"]
        ET.SubElement(name, self._tag("material")).text = filament["material"]
        ET.SubElement(name, self._tag("color")).text = filament["color_name"]
        ET.SubElement(metadata, self._tag("GUID")).text = filament["guid"]
        ET.SubElement(metadata, self._tag("version")).text = filament["version"]
        ET.SubElement(metadata, self._tag("color_code")).text = filament["color_code"]
        ET.SubElement(metadata, self._tag("description")).text = filament["description"]
        ET.SubElement(metadata, self._tag("adhesion_info")).text = ""

        properties = ET.SubElement(root, self._tag("properties"))
        ET.SubElement(properties, self._tag("density")).text = filament["density"]
        ET.SubElement(properties, self._tag("diameter")).text = filament["diameter"]
        if filament["weight"] is not None:
            ET.SubElement(properties, self._tag("weight")).text = filament["weight"]

        settings = ET.SubElement(root, self._tag("settings"))
        default_settings = [
            ("print cooling", "100"),
            ("relative extrusion", "1.0"),
            ("retract compensation", "0"),
        ]
        if filament["print_temperature"] is not None:
            default_settings.append(("print temperature", filament["print_temperature"]))
        if filament["standby_temperature"] is not None:
            default_settings.append(("standby temperature", filament["standby_temperature"]))
        if filament["bed_temperature"] is not None:
            default_settings.append(("heated bed temperature", filament["bed_temperature"]))

        for key, value in default_settings:
            setting = ET.SubElement(settings, self._tag("setting"), {"key": key})
            setting.text = value

        if hasattr(ET, "indent"):
            ET.indent(root, space="    ")

        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    def _build_description(self, filament: Dict[str, Any]) -> str:
        description_parts = [f"Imported from Spoolman filament {filament.get('id')}"]
        comment = self._clean_text(filament.get("comment"))
        article_number = self._clean_text(filament.get("article_number"))
        external_id = self._clean_text(filament.get("external_id"))

        if comment:
            description_parts.append(comment)
        if article_number:
            description_parts.append(f"Article number: {article_number}")
        if external_id:
            description_parts.append(f"External ID: {external_id}")

        return " | ".join(description_parts)

    def _derive_color_name(self, filament: Dict[str, Any], display_name: str) -> str:
        color_hex = self._normalize_color_code(filament.get("color_hex"), filament.get("multi_color_hexes"))
        if display_name:
            return display_name
        if color_hex != "#808080":
            return color_hex
        return "Imported"

    def _normalize_color_code(self, color_hex: Any, multi_color_hexes: Any) -> str:
        if isinstance(color_hex, str):
            normalized = self._normalize_single_color(color_hex)
            if normalized is not None:
                return normalized

        if isinstance(multi_color_hexes, str):
            first_color = multi_color_hexes.split(",", 1)[0]
            normalized = self._normalize_single_color(first_color)
            if normalized is not None:
                return normalized

        return "#808080"

    def _normalize_single_color(self, value: str) -> Optional[str]:
        normalized = value.strip().lstrip("#")
        if len(normalized) not in (6, 8):
            return None
        if not re.fullmatch(r"[0-9a-fA-F]{6}([0-9a-fA-F]{2})?", normalized):
            return None
        return f"#{normalized[:6].lower()}"

    def _write_bytes(self, file_path: str, payload: bytes) -> None:
        temp_path = f"{file_path}.tmp"
        with open(temp_path, "wb") as stream:
            stream.write(payload)
        os.replace(temp_path, file_path)

    def _tag(self, name: str) -> str:
        return f"{{{_MATERIAL_NS}}}{name}"

    def _slugify(self, value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
        return normalized or "spoolman_material"

    def _clean_text(self, value: Any, fallback: Optional[str] = None) -> Optional[str]:
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
        return fallback

    def _to_float(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return None

    def _format_number(self, value: float) -> str:
        if value is None:
            return ""
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.4f}".rstrip("0").rstrip(".")
