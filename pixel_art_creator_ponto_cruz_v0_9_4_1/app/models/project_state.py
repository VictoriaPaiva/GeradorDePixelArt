
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import json


STEP_KEYS = [
    "input",
    "matrix_art",
    "matrix",
    "palette",
    "simplification",
    "manual",
    "pattern",
    "export",
]
@dataclass
class ProjectState:
    project_name: str = "Novo projeto"
    project_file: Optional[str] = None

    source_image_path: Optional[str] = None
    ai_image_path: Optional[str] = None
    matrix_image_path: Optional[str] = None
    simplified_image_path: Optional[str] = None
    edited_matrix_path: Optional[str] = None
    pattern_image_path: Optional[str] = None

    matrix_size: int = 100
    palette_target: int = 50

    approvals: dict = field(default_factory=lambda: {k: False for k in STEP_KEYS})
    metadata: dict = field(default_factory=dict)

    dirty: bool = False

    def approve(self, step_key: str):
        self.approvals[step_key] = True
        self.dirty = True

    def unapprove(self, step_key: str):
        self.approvals[step_key] = False
        self.dirty = True

    def invalidate_after(self, step_key: str):
        """Invalidate all stages that depend on the changed stage."""
        if step_key not in STEP_KEYS:
            return
        idx = STEP_KEYS.index(step_key)
        for k in STEP_KEYS[idx + 1:]:
            self.approvals[k] = False

        if idx < STEP_KEYS.index("matrix_art"):
            self.metadata.pop("chat_matrix_art_path", None)
            self.metadata.pop("chat_matrix_art_origin", None)
            self.metadata.pop("chat_matrix_prompt", None)

        if idx < STEP_KEYS.index("matrix"):
            self.matrix_image_path = None
            self.metadata.pop("matrix_100x100_png", None)
            self.metadata.pop("matrix_png", None)
            self.metadata.pop("matrix_source_path", None)
            self.metadata.pop("matrix_method", None)
            self.metadata.pop("matrix_width", None)
            self.metadata.pop("matrix_height", None)

        if idx < STEP_KEYS.index("simplification"):
            self.simplified_image_path = None
            self.metadata.pop("simplified_50_png", None)
            self.metadata.pop("simplified_png", None)
            self.metadata.pop("final_palette_50", None)
            self.metadata.pop("final_essential_colors", None)
            self.metadata.pop("simplification_input_signature", None)
            self.metadata.pop("simplification_method", None)

        if idx < STEP_KEYS.index("manual"):
            self.edited_matrix_path = None
            self.metadata.pop("edited_100x100_png", None)
            self.metadata.pop("edited_matrix_png", None)
            self.metadata.pop("manual_source_signature", None)

        if idx < STEP_KEYS.index("pattern"):
            self.pattern_image_path = None
            self.metadata.pop("pattern_generated", None)
            self.metadata.pop("pattern_source_signature", None)
            self.metadata.pop("pattern_entries", None)
            self.metadata.pop("legend_image_path", None)

        if idx < STEP_KEYS.index("export"):
            self.metadata.pop("export_manifest", None)
            self.metadata.pop("export_source_signature", None)

        self.dirty = True

    def to_dict(self):
        d = asdict(self)
        d["dirty"] = False
        return d

    @classmethod
    def from_dict(cls, data):
        obj = cls()
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        # Migration from projects created while the application had a
        # separate AI stage. The Pixel Art from that stage becomes the
        # imported image of the new first stage.
        if obj.ai_image_path and data.get("approvals", {}).get("ai", False):
            obj.source_image_path = obj.ai_image_path
            obj.approvals["input"] = True

        # Remove obsolete approval keys while ensuring current steps exist.
        obj.approvals = {
            key: bool(obj.approvals.get(key, False))
            for key in STEP_KEYS
        }

        for key in STEP_KEYS:
            obj.approvals.setdefault(key, False)

        obj.dirty = False
        return obj

    def save(self, path: str):
        path = str(Path(path))
        self.project_file = path
        payload = self.to_dict()
        payload["project_file"] = path
        Path(path).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        self.dirty = False

    @classmethod
    def load(cls, path: str):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        obj = cls.from_dict(payload)
        obj.project_file = str(Path(path))
        return obj
