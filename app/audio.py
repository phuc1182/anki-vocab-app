from __future__ import annotations

from pathlib import Path

import edge_tts

from .validator import validate_nonempty_file


async def create_audio(text: str, output_path: Path, voice: str) -> None:
	if output_path.exists() and output_path.stat().st_size > 0:
		return

	communicator = edge_tts.Communicate(text=text, voice=voice)
	await communicator.save(str(output_path))
	validate_nonempty_file(output_path, "audio file")
