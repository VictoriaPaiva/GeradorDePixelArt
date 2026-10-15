
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import json


STEP_KEYS = [
    "input",
    "ai",
    "palette",
    "essential",
    "matrix",
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

        # Clear only derived paths after the relevant stage.
        if idx < STEP_KEYS.index("ai"):
            self.ai_image_path = None
        if idx < STEP_KEYS.index("matrix"):
            self.matrix_image_path = None
            self.metadata.pop("matrix_100x100_png", None)
            self.metadata.pop("matrix_source_path", None)
            self.metadata.pop("matrix_method", None)
        if idx < STEP_KEYS.index("simplification"):
            self.simplified_image_path = None
            self.metadata.pop("simplified_50_png", None)
            self.metadata.pop("final_palette_50", None)
            self.metadata.pop("final_essential_colors", None)
            self.metadata.pop("simplification_input_signature", None)
            self.metadata.pop("simplification_method", None)
        if idx < STEP_KEYS.index("manual"):
            self.edited_matrix_path = None
            self.metadata.pop("edited_100x100_png", None)
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
        # Ensure new steps exist if an old project file is opened later.
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
