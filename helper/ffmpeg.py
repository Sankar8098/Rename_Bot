import os
import math
import re
import json
import subprocess
import time
import asyncio
from configs import Config
from typing import Tuple
from humanfriendly import format_timespan
from core.display_progress import TimeFormatter
from pyrogram.errors.exceptions.flood_420 import FloodWait

async def vidmark(the_media, message, working_dir, watermark_path, output_vid, total_time, logs_msg, status, mode, position, size):
    file_genertor_command = [
        "ffmpeg", "-hide_banner", "-loglevel", "quiet", "-progress", working_dir, "-i", the_media, "-i", watermark_path,
        "-filter_complex", f"[1][0]scale2ref=w='iw*{size}/100':h='ow/mdar'[wm][vid];[vid][wm]overlay={position}",
        "-c:v", "copy", "-preset", mode, "-crf", "0", "-c:a", "copy", output_vid
    ]
    COMPRESSION_START_TIME = time.time()
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    with open(status, 'r+') as f:
        statusMsg = json.load(f)
        statusMsg['pid'] = process.pid
        f.seek(0)
        json.dump(statusMsg, f, indent=2)
    while process.returncode != 0:
        await asyncio.sleep(5)
        with open(working_dir, 'r+') as file:
            text = file.read()
            frame = re.findall("frame=(\d+)", text)
            time_in_us=re.findall("out_time_ms=(\d+)", text)
            progress=re.findall("progress=(\w+)", text)
            speed=re.findall("speed=(\d+\.?\d*)", text)
            if len(frame):
                frame = int(frame[-1])
            else:
                frame = 1
            if len(speed):
                speed = speed[-1]
            else:
                speed = 1
            if len(time_in_us):
                time_in_us = time_in_us[-1]
            else:
                time_in_us = 1
            if len(progress):
                if progress[-1] == "end":
                    break
            execution_time = TimeFormatter((time.time() - COMPRESSION_START_TIME)*1000)
            elapsed_time = int(time_in_us)/1000000
            difference = math.floor( (total_time - elapsed_time) / float(speed) )
            ETA = "-"
            if difference > 0:
                ETA = TimeFormatter(difference*1000)
            percentage = math.floor(elapsed_time * 100 / total_time)
            progress_str = "๐“ **Progress:** {0}%\n`[{1}{2}]`".format(
                round(percentage, 2),
                ''.join(["โ–“" for i in range(math.floor(percentage / 10))]),
                ''.join(["โ–‘" for i in range(10 - math.floor(percentage / 10))])
                )
            stats = f'๐“ฆ๏ธ **Adding Watermark [Preset: `{mode}`]**\n\n' \
                    f'โฐ๏ธ **ETA:** `{ETA}`\nโ๏ธ **Position:** `{position}`\n๐”ฐ **PID:** `{process.pid}`\n๐” **Duration: `{format_timespan(total_time)}`**\n\n' \
                    f'{progress_str}\n'
            try:
                await logs_msg.edit(text=stats)
                await message.edit(text=stats)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                pass
            except:
                pass
        
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    print(e_response)
    print(t_response)
    if os.path.lexists(output_vid):
        return output_vid
    else:
        return None

async def take_screen_shot(video_file, output_directory, ttl):
    out_put_file_name = output_directory + \
        "/" + str(time.time()) + ".jpg"
    file_genertor_command = [
        "ffmpeg",
        "-ss",
        str(ttl),
        "-i",
        video_file,
        "-vframes",
        "1",
        out_put_file_name
    ]
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None

