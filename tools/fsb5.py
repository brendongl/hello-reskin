"""Minimal FMOD FSB5 writer (single PCM16 mono/stereo sample), matching Unity's PCM AudioClips."""
import struct
import numpy as np

FREQ_IDX = {8000: 1, 11000: 2, 11025: 3, 16000: 4, 22050: 5, 24000: 6, 32000: 7, 44100: 8, 48000: 9}

def make_fsb_pcm16(pcm: np.ndarray, rate: int, channels: int = 1, loop=None) -> bytes:
    pcm = np.asarray(pcm, dtype='<i2')
    nsamples = len(pcm) // channels
    data = pcm.tobytes()
    data += b'\0' * ((-len(data)) % 32)
    bits = ((1 if loop else 0)                 # extra chunk flag (loop points)
            | (FREQ_IDX[rate] << 1)
            | ((channels - 1) << 5)
            | (0 << 6)                         # data offset (16-byte units)
            | (nsamples << 34))
    shdr = struct.pack('<Q', bits)
    if loop:   # chunk type 3 = loop start/end (samples), as in the game's own music clips
        shdr += struct.pack('<I', (8 << 1) | (3 << 25)) + struct.pack('<II', *loop)
    shdr += b'\0' * (36 - len(shdr))              # 36 bytes -> data starts at 96, like the game's files
    header = (b'FSB5' + struct.pack('<IIIIII', 1, 1, len(shdr), 0, len(data), 2)
              + b'\0' * 8 + b'\0' * 16 + b'\0' * 8)
    assert len(header) == 60
    return header + shdr + data
