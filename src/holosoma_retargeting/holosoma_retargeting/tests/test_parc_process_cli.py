from pathlib import Path

from holosoma_retargeting.examples.parc_process import build_arg_parser


def test_parc_process_cli_accepts_source_and_output_paths() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--sample",
            "/tmp/sample.pkl",
            "--source-xml",
            "/tmp/humanoid.xml",
            "--output-root",
            "/tmp/out",
        ]
    )
    assert isinstance(args.sample, Path)
    assert str(args.sample).endswith("sample.pkl")
    assert str(args.source_xml).endswith("humanoid.xml")
    assert str(args.output_root).endswith("out")
