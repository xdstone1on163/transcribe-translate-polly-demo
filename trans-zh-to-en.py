import asyncio

# This example uses the sounddevice library to get an audio stream from the
# microphone. It's not a dependency of the project but can be installed with
# `pip install sounddevice`.
import sounddevice

import sys
from contextlib import closing
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
import boto3
import pyaudio
from botocore.exceptions import BotoCoreError, ClientError
translate = boto3.client(service_name='translate', region_name='ap-northeast-1', use_ssl=True)
polly = boto3.client('polly', region_name='ap-northeast-1')
SAMPLE_RATE = 16000
READ_CHUNK = 1024*2
CHANNELS = 1
BYTES_PER_SAMPLE = 2

"""
Here's an example of a custom event handler you can extend to
process the returned transcription results as needed. This
handler will simply print the text out to your interpreter.
"""


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        # This handler can be implemented to handle transcriptions as needed.
        # Here's an example to get started.
        results = transcript_event.transcript.results
        if len(results) > 0:
            for result in results:
                if result.is_partial:
                    continue
                else:
                    for alt in result.alternatives:
                        print('中文:  ',alt.transcript)
                        res = translate.translate_text(Text=alt.transcript,
                                                          SourceLanguageCode="zh", TargetLanguageCode="en")
                        # print(res)
                        print('英文:   ' + res.get('TranslatedText'))
                        # print('SourceLanguageCode: ' + res.get('SourceLanguageCode'))
                        # print('TargetLanguageCode: ' + res.get('TargetLanguageCode'))
                        try:
                            response = polly.synthesize_speech(Text=res.get('TranslatedText'),VoiceId="Joanna",
                                                               # LanguageCode="en-US",
                                                               OutputFormat="pcm",
                                                               SampleRate=str(SAMPLE_RATE))
                            # print(response)
                        except (BotoCoreError, ClientError) as error:
                            print(error)
                            # sys.exit(-1)
                        print('开始同传发音...')
                        p = pyaudio.PyAudio()
                        stream = p.open(format=p.get_format_from_width(BYTES_PER_SAMPLE),
                                        channels=CHANNELS,
                                        rate=SAMPLE_RATE,
                                        output=True)
                        with closing(response["AudioStream"]) as polly_stream:
                            while True:
                                data = polly_stream.read(READ_CHUNK)
                                # print(data)
                                if data == b'':
                                    break
                                stream.write(data)
                        stream.stop_stream()
                        stream.close()
                        p.terminate()
                        print("========同传完成========\n")

async def mic_stream():
    # This function wraps the raw input stream from the microphone forwarding
    # the blocks to an asyncio.Queue.
    loop = asyncio.get_event_loop()
    input_queue = asyncio.Queue()

    def callback(indata, frame_count, time_info, status):
        loop.call_soon_threadsafe(input_queue.put_nowait, (bytes(indata), status))

    # Be sure to use the correct parameters for the audio stream that matches
    # the audio formats described for the source language you'll be using:
    # https://docs.aws.amazon.com/transcribe/latest/dg/streaming.html
    stream = sounddevice.RawInputStream(
        channels=1,
        samplerate=16000,
        callback=callback,
        blocksize=1024 * 2,
        dtype="int16",
    )
    # Initiate the audio stream and asynchronously yield the audio chunks
    # as they become available.
    with stream:
        while True:
            indata, status = await input_queue.get()
            yield indata, status


async def write_chunks(stream):
    # This connects the raw audio chunks generator coming from the microphone
    # and passes them along to the transcription stream.
    async for chunk, status in mic_stream():
        await stream.input_stream.send_audio_event(audio_chunk=chunk)
    await stream.input_stream.end_stream()


async def basic_transcribe():
    # Setup up our client with our chosen AWS region
    print('正在建立连接...')
    client = TranscribeStreamingClient(region="ap-northeast-1")
    print('============================')
    print('连接已经建立，可以开始讲话了。')
    print('\n')


    # Start transcription to generate our async stream
    stream = await client.start_stream_transcription(
        language_code="zh-CN",
        media_sample_rate_hz=16000,
        media_encoding="pcm",
    )

    # Instantiate our handler and start processing events
    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(write_chunks(stream), handler.handle_events())


loop = asyncio.get_event_loop()
loop.run_until_complete(basic_transcribe())
loop.close()