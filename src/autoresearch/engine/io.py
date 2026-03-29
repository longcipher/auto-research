"""Async I/O utilities for non-blocking file operations."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import orjson


async def async_read_text(path: Path, encoding: str = "utf-8") -> str:
    """Asynchronously read text from a file.

    Args:
        path: Path to the file to read
        encoding: Text encoding (default: utf-8)

    Returns:
        The file contents as a string
    """
    return await asyncio.to_thread(path.read_text, encoding=encoding)


async def async_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Asynchronously write text to a file.

    Args:
        path: Path to the file to write
        content: Text content to write
        encoding: Text encoding (default: utf-8)
    """
    await asyncio.to_thread(path.write_text, content, encoding=encoding)


async def async_read_bytes(path: Path) -> bytes:
    """Asynchronously read bytes from a file.

    Args:
        path: Path to the file to read

    Returns:
        The file contents as bytes
    """
    return await asyncio.to_thread(path.read_bytes)


async def async_write_bytes(path: Path, content: bytes) -> None:
    """Asynchronously write bytes to a file.

    Args:
        path: Path to the file to write
        content: Binary content to write
    """
    await asyncio.to_thread(path.write_bytes, content)


async def async_write_json(path: Path, data: Any, *, indent: bool = True) -> None:
    """Asynchronously write JSON to a file.

    Args:
        path: Path to the file to write
        data: JSON-serializable data to write
        indent: Whether to indent the output (default: True)
    """
    opts = orjson.OPT_INDENT_2 if indent else 0
    content = orjson.dumps(data, option=opts)
    await async_write_bytes(path, content)


async def async_read_json(path: Path) -> Any:
    """Asynchronously read JSON from a file.

    Args:
        path: Path to the JSON file to read

    Returns:
        The parsed JSON data
    """
    content = await async_read_bytes(path)
    return orjson.loads(content)


async def async_mkdir(path: Path, *, parents: bool = True, exist_ok: bool = True) -> None:
    """Asynchronously create a directory.

    Args:
        path: Path to the directory to create
        parents: Whether to create parent directories (default: True)
        exist_ok: Whether to ignore if directory already exists (default: True)
    """
    await asyncio.to_thread(path.mkdir, parents=parents, exist_ok=exist_ok)


async def async_exists(path: Path) -> bool:
    """Asynchronously check if a path exists.

    Args:
        path: Path to check

    Returns:
        True if the path exists, False otherwise
    """
    return await asyncio.to_thread(path.exists)


class AsyncFileWriter:
    """Utility class for async file operations with common directory handling."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    async def write_text(self, relative_path: str, content: str, encoding: str = "utf-8") -> Path:
        """Write text to a file relative to the base directory.

        Args:
            relative_path: Relative path from base_dir
            content: Text content to write
            encoding: Text encoding (default: utf-8)

        Returns:
            The full path to the written file
        """
        path = self._base_dir / relative_path
        await async_mkdir(path.parent, parents=True, exist_ok=True)
        await async_write_text(path, content, encoding=encoding)
        return path

    async def write_json(self, relative_path: str, data: Any, *, indent: bool = True) -> Path:
        """Write JSON to a file relative to the base directory.

        Args:
            relative_path: Relative path from base_dir
            data: JSON-serializable data to write
            indent: Whether to indent the output (default: True)

        Returns:
            The full path to the written file
        """
        path = self._base_dir / relative_path
        await async_mkdir(path.parent, parents=True, exist_ok=True)
        await async_write_json(path, data, indent=indent)
        return path

    async def write_bytes(self, relative_path: str, content: bytes) -> Path:
        """Write bytes to a file relative to the base directory.

        Args:
            relative_path: Relative path from base_dir
            content: Binary content to write

        Returns:
            The full path to the written file
        """
        path = self._base_dir / relative_path
        await async_mkdir(path.parent, parents=True, exist_ok=True)
        await async_write_bytes(path, content)
        return path
