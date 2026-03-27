# tests/test_cdp.py
import pytest
import json
import tempfile
from pathlib import Path
from manzhou_lapian.cdp import CDPReader
from manzhou_lapian.types import CDPData


def test_read_valid_cdp():
    cdp_data = {
        "characters": {
            "char_01_谭斌": {"name": "谭斌", "description": "女，26岁，黑色职业套装。"},
            "char_02_潘总": {"name": "潘总", "description": "男，40岁，深色西装。"},
        },
        "locations": {
            "loc_01_办公室": {"name": "CBD办公室", "description": "落地窗，灰色地毯。"},
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cdp_data, f)
        path = f.name

    reader = CDPReader(path)
    result = reader.read()

    assert isinstance(result, CDPData)
    assert "char_01_谭斌" in result.characters
    assert "loc_01_办公室" in result.locations
    ctx = result.get_context()
    assert "【【char_01_谭斌】】" in ctx
    assert "【【loc_01_办公室】】" in ctx

    Path(path).unlink()


def test_read_missing_file():
    reader = CDPReader("/nonexistent/path.json")
    result = reader.read()
    assert isinstance(result, CDPData)
    assert result.characters == {}
    assert "无CDP上下文" in result.get_context()
