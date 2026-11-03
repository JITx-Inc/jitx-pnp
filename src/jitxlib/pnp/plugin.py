"""JITX export plugin: write a pick-and-place file from a design.

Registration is an import side effect of the decorator, reached through the
`jitx-plugin` entry point. The CLI derives its flags from the keyword
parameters of `export`, so everything settable from the command line is a
flat scalar; a caller that needs more - to be told which files were written -
uses `jitxlib.pnp.pick_and_place` directly.
"""

from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, override

import jitx.log
import jitx.plugin

from .format.rotation import BottomRotation
from .format.write import TableFormat

if TYPE_CHECKING:
    from jitx.run import RuntimeDesign

logger = getLogger(__name__)

# No `from __future__ import annotations` in this module, deliberately. The
# CLI builds its options from `inspect.signature(plugin.export)`, and with
# postponed evaluation every annotation arrives as a string that typer
# cannot resolve - which fails the whole `design export` command group, not
# just this plugin.


@jitx.plugin.Export.register("pnp")
class PnpExport(jitx.plugin.Export):
    """Export a pick-and-place file."""

    @override
    def preflight(
        self,
        *,
        output: Path | None = None,
        format: TableFormat = TableFormat.CSV,
        split_sides: bool = False,
        bottom_rotation: BottomRotation = BottomRotation.NATIVE,
        include_unsoldered: bool = False,
        overwrite: bool = False,
    ) -> None:
        """Reject an unusable output path before the design is built.

        The format and the convention need no checking here: typer rejects a
        value outside the enum before this runs. The output guard covers a
        single file that was named outright. Splitting decides its paths
        from which sides turn out to be populated, and the writer is where
        that is known, so guarding it here would reject a run over a file it
        was never going to write.

        Args:
            output: the only flag acted on here. The rest are carried
                because the CLI passes the same keywords to this and to
                `export`.
            overwrite: permission to replace what is already there.
            split_sides: whether the paths are decided later.
        """
        if output is None or overwrite or split_sides:
            return
        path = Path(output).absolute()
        if path.is_dir():
            raise ValueError(f"Output path {path} is a directory")
        if path.exists():
            raise ValueError(
                f"Output path {path} already exists and overwrite was not specified"
            )

    @override
    def export(
        self,
        design: "RuntimeDesign",
        *,
        output: Path | None = None,
        format: TableFormat = TableFormat.CSV,
        split_sides: bool = False,
        bottom_rotation: BottomRotation = BottomRotation.NATIVE,
        include_unsoldered: bool = False,
        overwrite: bool = False,
    ) -> None:
        from . import pick_and_place

        written = pick_and_place(
            design,
            output=output,
            format=format,
            split_sides=split_sides,
            bottom_rotation=bottom_rotation,
            include_unsoldered=include_unsoldered,
            overwrite=overwrite,
        )
        # notice level so the result reaches both the console and the run's
        # log file, unlike print
        jitx.log.notice(
            logger,
            "Wrote %s",
            ", ".join(str(path) for path in written),
        )
