import subprocess
import sys

import pytest

from jitx_pnp.__main__ import main


def test_main_prints_csv_to_stdout(synthetic_xml, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["jitx-pnp", str(synthetic_xml)])
    main()
    captured = capsys.readouterr()
    assert captured.out.startswith("RefDes,X,Y,Rotation,PN,Package,Side")


def test_main_writes_to_output_file(synthetic_xml, tmp_path, monkeypatch, capsys):
    out = tmp_path / "pnp.csv"
    monkeypatch.setattr(sys, "argv", ["jitx-pnp", str(synthetic_xml), "-o", str(out)])
    main()
    assert out.exists()
    # Stdout should be empty when writing to a file.
    captured = capsys.readouterr()
    assert captured.out == ""


def test_main_format_flag_selects_tsv(synthetic_xml, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["jitx-pnp", str(synthetic_xml), "-f", "tsv"])
    main()
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0].count("\t") >= 6


def test_main_split_sides_requires_output(synthetic_xml, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jitx-pnp", str(synthetic_xml), "--split-sides"])
    with pytest.raises(SystemExit):
        main()


def test_main_split_sides_writes_per_side_files(synthetic_xml, tmp_path, monkeypatch):
    out = tmp_path / "pnp.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        ["jitx-pnp", str(synthetic_xml), "-o", str(out), "--split-sides"],
    )
    main()
    assert (tmp_path / "pnp_top.csv").exists()
    assert (tmp_path / "pnp_bottom.csv").exists()


def test_main_help_exits_zero(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jitx-pnp", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_module_invocation_works(synthetic_xml):
    # `python -m jitx_pnp <xml>` should produce the same first line as the API.
    result = subprocess.run(
        [sys.executable, "-m", "jitx_pnp", str(synthetic_xml)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.splitlines()[0] == "RefDes,X,Y,Rotation,PN,Package,Side"
