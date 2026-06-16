"""Audio setup for Qualcomm Codec on QCM2290 hardware.

Configures ALSA mixer paths for LineOut playback and SoundWire mic capture,
then writes a system-wide ``/etc/asound.conf`` for automatic sample-rate
conversion (QCM2290 native 48 kHz → application rate).
"""

import logging
import subprocess

logger = logging.getLogger(__name__)


def setup_audio_output():
    """Configure Qualcomm Codec ALSA mixer for LineOut playback + SoundWire mic capture.

    - Playback path: MultiMedia2 -> LO_RDAC (LineOut)  → hw:0,1
    - Capture path:  MultiMedia3 <- SWR_MIC (SoundWire) → hw:0,2

    Writes a system-wide ``/etc/asound.conf`` so PyAudio can find the output
    device with automatic sample-rate conversion for the QCM2290 hardware
    (48 kHz native).
    """

    def _amix(cmd, *args):
        subprocess.run(["amixer", "-D", "hw:0", cmd] + list(args),
                       capture_output=True)

    # Note: PipeWire must be stopped on the HOST before starting the app,
    # otherwise it holds hw:0,0 and hw:0,2, blocking container ALSA access.
    # Run on host: systemctl --user stop pipewire pipewire-pulse wireplumber

    # Capture path must be configured BEFORE playback path.
    # Reason: MultiMedia2 (hw:0,1) is used for playback, MultiMedia3 (hw:0,2)
    # for capture. We configure capture first so the playback mixer state
    # (on MultiMedia2's RX side) is not affected.
    #
    # --- Capture path: MultiMedia3 ← SWR_MIC (SoundWire microphone) ---
    _amix("cset", "iface=MIXER,name='MultiMedia3 Mixer TX_CODEC_DMA_TX_3'", "1")
    _amix("cset", "iface=MIXER,name='TX DEC0 MUX'", "SWR_MIC")
    _amix("cset", "iface=MIXER,name='TX SMIC MUX0'", "SWR_MIC1")
    _amix("cset", "iface=MIXER,name='TX_AIF1_CAP Mixer DEC0'", "1")
    _amix("cset", "iface=MIXER,name='ADC2 Switch'", "1")
    _amix("sset", "ADC2 Volume", "7")
    _amix("cset", "iface=MIXER,name='ADC2_MIXER Switch'", "1")
    _amix("cset", "iface=MIXER,name='ADC2 MUX'", "INP2")
    _amix("sset", "TX_DEC0 Volume", "80")

    # --- Playback path: MultiMedia2 → LO_RDAC (LineOut) ---
    _amix("sset", "RX_CODEC_DMA_RX_0 Audio Mixer MultiMedia2", "on")
    _amix("cset", "iface=MIXER,name='RX_MACRO RX0 MUX'", "1")
    _amix("cset", "iface=MIXER,name='RX INT0_1 MIX1 INP0'", "RX0")
    _amix("cset", "iface=MIXER,name='RX INT0 DEM MUX'", "1")
    _amix("sset", "LO_RDAC", "on")
    _amix("sset", "HPHL", "on")
    _amix("sset", "RX_RX0 Digital", "37")
    _amix("sset", "RX_RX1 Digital", "37")

    # /etc/asound.conf is written at image build time by the Dockerfile.
    logger.info("Audio: Playback hw:0,1 (MultiMedia2) + Capture hw:0,2 (MultiMedia3) ready")
