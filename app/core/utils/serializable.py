from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _serialize(v:Any) -> Any:
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


class Serializable:
    """Mixin that adds to_dict() and to_json() serialization to any class."""

    def to_dict(self) -> dict[str, Any]:
        return {
            k: v for k, v in vars(self).items()
            if not k.startswith(("_", "<", "s_id"))
        }

    def to_json(self) -> dict[str, Any]:
        return {k: _serialize(v) for k, v in self.to_dict().items()}
