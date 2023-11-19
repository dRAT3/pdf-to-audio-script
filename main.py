import asyncio

import os
from pathlib import Path
from datetime import datetime

from openai import AsyncOpenAI

import PyPDF2
from pydub import AudioSegment

import settings
import helpers
    
async def clean_page(page_text):
    page_text = helpers.remove_extra_whitespaces(page_text)

    if settings.USE_GPT_3_5_TO_CLEAN:
        page_text = await helpers.clean_up_text_with_3_5_turbo(page_text)

    return page_text
    
async def text_to_speech(cleaned_text, out_file_name, working_dir):
    client = AsyncOpenAI()
    # Define the full path for the speech file
    speech_file_path = working_dir / out_file_name

    print(f"Transcribing: {out_file_name}")
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=cleaned_text
    )

    response.stream_to_file(speech_file_path)


async def process_page(page_number, page_text, in_file_path, out_file_dir):
    print(f"Cleaning page {page_number}")
    cleaned_text = await clean_page(page_text)
    
    
    base_name = os.path.basename(in_file_path)
    base_name, _ = os.path.splitext(base_name)
    out_file_name = base_name + "_page_" + str(page_number) + ".mp3"

    await text_to_speech(cleaned_text, out_file_name, out_file_dir)

async def main():
    ### Change settings.py before using this script! ###

    # Create the output directory
    out_file_path = Path(settings.OUT_FILE_PATH)
    out_file_path.mkdir(parents=True, exist_ok=True)
    
    # Create the working directory for this execution
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    working_dir = out_file_path / current_datetime
    working_dir.mkdir(parents=True, exist_ok=True)

    # Will create a task as soon as a page is extracted and send it off for processing
    tasks = []
    with open(settings.FILE_PATH_PDF, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        for page_number in range(settings.START_PAGE, settings.END_PAGE):
            page_text = reader.pages[page_number].extract_text()
            task = asyncio.create_task(
                    process_page(
                        page_number,
                        page_text,
                        settings.FILE_PATH_PDF,
                        working_dir,
                    ))
            tasks.append(task)


    await asyncio.gather(*tasks)

    # Here you can implement the reassembly logic based on file naming

asyncio.run(main())
