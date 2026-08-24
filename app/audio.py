from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts

from .validator import validate_nonempty_file


async def create_audio(text: str, output_path: Path, voice: str) -> None:
	text = text.strip()
	if not text:
		raise ValueError(f"Cannot create audio for empty text: {output_path.name}")

	if output_path.exists() and output_path.stat().st_size > 0:
		return

	last_error: Exception | None = None
	for attempt in range(3):
		try:
			output_path.unlink(missing_ok=True)
			communicator = edge_tts.Communicate(text=text, voice=voice)
			await communicator.save(str(output_path))
			validate_nonempty_file(output_path, "audio file")
			return
		except Exception as exc:
			last_error = exc
			output_path.unlink(missing_ok=True)
			if attempt < 2:
				await asyncio.sleep(1)

	raise RuntimeError(
		f"Không thể tạo audio cho '{text}'. Edge TTS không trả về audio sau 3 lần thử."
	) from last_error
