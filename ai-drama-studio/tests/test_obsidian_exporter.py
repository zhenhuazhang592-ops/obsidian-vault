# tests/test_obsidian_exporter.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile
from manzhou_lapian.types import LapianResult, ShotAnalysis, AudioLayer
from manzhou_lapian.exporters.obsidian import ObsidianExporter


def test_export_basic(tmp_path):
    """测试生成 Obsidian 笔记"""
    result = LapianResult(
        video_path="/test.mp4",
        video_id="test123",
        video_duration=157.0,
        total_shots=2,
        analysis_model="gemini",
        scene_threshold=27.0,
        shots=[
            ShotAnalysis(
                shot_number=1,
                start_time=0.0,
                end_time=8.0,
                duration=8.0,
                shot_size="MS",
                camera_angle="平视",
                camera_movement="固定",
                lighting_style="自然光",
                description="【【char_01_谭斌】】站在落地窗前。",
                dialogue="无",
                audio_layer=AudioLayer(),
            ),
            ShotAnalysis(
                shot_number=2,
                start_time=8.0,
                end_time=15.0,
                duration=7.0,
                shot_size="MCU",
                camera_angle="平视",
                camera_movement="固定",
                lighting_style="侧逆光",
                description="【【char_01_谭斌】】低头看手机。",
                dialogue="这周必须签约了。",
                audio_layer=AudioLayer(music="piano-8-15s"),
            ),
        ],
        output_dir=str(tmp_path),
        video_filename="格子间女人-第01集.mp4",
    )

    exporter = ObsidianExporter()
    output_path = exporter.export(result)

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "# 格子间女人-第01集 拉片分析" in content
    assert "char_01_谭斌" in content
    assert "MS" in content
    assert "157" in content
    assert "## 分镜总览" in content
    assert "## 镜 01" in content
    assert "## 镜 02" in content
    assert "piano-8-15s" in content  # Audio Layer


def test_frontmatter(tmp_path):
    """测试 frontmatter 字段"""
    result = LapianResult(
        video_path="/test.mp4",
        video_id="test456",
        video_duration=30.0,
        total_shots=1,
        analysis_model="gemini",
        scene_threshold=27.0,
        shots=[],
        output_dir=str(tmp_path),
        video_filename="test.mp4",
    )
    exporter = ObsidianExporter()
    output_path = exporter.export(result)
    content = output_path.read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "uid:" in content
    assert "title:" in content
    assert "created:" in content
    assert "tags:" in content
