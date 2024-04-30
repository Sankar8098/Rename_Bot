import os
import math
import re
import json
import subprocess
import time
import asyncio
from typing import Tuple
from humanfriendly import format_timespan
from core.display_progress import TimeFormatter
from pyrogram.errors.exceptions.flood_420 import FloodWait


async def vidmark(
    the_media,
    message,
    working_dir,
    watermark_path,
    output_vid,
    total_time,
    logs_msg,
    status,
    mode,
    position,
    size
):
    # Command to add a watermark to the video
    file_generator_command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "quiet",
        "-progress",
        working_dir,
        "-i",
        the_media,
        "-i",
        watermark_path,
        "-filter_complex",
        f"[1][0]scale2ref=w='iw*{size}/100':h='ow/mdar'[wm][vid];[vid][wm]overlay={position}",
        "-c:v",
        "copy",
        "-preset",
        mode,
        "-crf",
        "0",
        "-c:a",
        "copy",
        output_vid,
    ]

    # Start subprocess to add watermark
    process = await asyncio.create_subprocess_exec(
        *file_generator_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Save process ID in status file
    with open(status, 'r+') as f:
        status_msg = json.load(f)
        status_msg['pid'] = process.pid
        f.seek(0)
        json.dump(status_msg, f, indent=2)

    COMPRESSION_START_TIME = time.time()

    while process.returncode is None:
        await asyncio.sleep(5)

        with open(working_dir, 'r+') as file:
            text = file.read()

            # Parse progress from ffmpeg output
            frame = re.findall("frame=(\d+)", text)
            time_in_us = re.findall("out_time_ms=(\d+)", text)
            progress = re.findall("progress=(\w+)", text)
            speed = re.findall("speed=(\d+\.?\d*)", text)

            # Handling missing or incomplete information
            frame = int(frame[-1]) if frame else 1
            speed = speed[-1] if speed else '1'
            time_in_us = int(time_in_us[-1]) if time_in_us else 1

            if progress and progress[-1] == "end":
                break

            # Calculate progress and ETA
            elapsed_time = time_in_us / 1_000_000
            difference = math.floor((total_time - elapsed_time) / float(speed))
            ETA = "-" if difference <= 0 else TimeFormatter(difference * 1000)

            percentage = math.floor((elapsed_time * 100) / total_time)
            progress_bar = "[" + "▓" * (percentage // 10) + "░" * (10 - (percentage // 10)) + "]"

            progress_str = f"**Progress:** {round(percentage, 2)}% {progress_bar}"
            stats = (
                f"**Adding Watermark [Preset: `{mode}`]**\n\n"
                f"**ETA:** `{ETA}`\n"
                f"**Position:** `{position}`\n"
                f"**PID:** `{process.pid}`\n"
                f"**Duration:** `{format_timespan(total_time)}`\n\n"
                f"{progress_str}\n"
            )

            # Attempt to update messages, handling FloodWait or other errors
            try:
                await logs_msg.edit(text=stats)
                await message.edit(text=stats)
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except Exception as e:
                print(f"An error occurred while updating progress: {e}")

    # After completion, read stdout and stderr
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()

    print("Stderr:", e_response)
    print("Stdout:", t_response)

    # Return the output video path if it exists
    if os.path.lexists(output_vid):
        return output_vid
    else:
        return None


async def take_screen_shot(
    video_file,
    output_directory,
    ttl
):
    # File name for the screenshot
    output_file_name = f"{output_directory}/{time.time()}.jpg"

    # Command to take a screenshot
    file_generator_command = [
        "ffmpeg",
        "-ss",
        str(ttl),
        "-i",
        video_file,
        "-vframes",
        "1",
        output_file_name,
    ]

    # Start subprocess to take the screenshot
    process = await asyncio.create_subprocess_exec(
        *file_generator_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Wait for the process to finish and get output
    stdout, stderr = await process.communicate()

    # Print error and success messages
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()

    print("Stderr:", e_response)
    print("Stdout:", t_response)

    # Return the screenshot path if it exists
    if os.path.lexists(output_file_name):
        return output_file_name
    else:
        return None
    
