"""Example: Waveform editor component using starelements with Peaks.js."""

import math
import struct

from starhtml import H1, Audio, Button, Div, P, Script, Span, Style, serve, star_app
from starlette.responses import Response

from starelements import Local, element


def generate_demo_wav(duration=10, sample_rate=44100):
    """Generate a WAV with layered tones and rhythm for an interesting waveform."""
    n = sample_rate * duration
    samples = []
    for i in range(n):
        t = i / sample_rate
        # Base: frequency sweep 220→440 Hz
        freq = 220 + 220 * (t / duration)
        val = 0.4 * math.sin(2 * math.pi * freq * t)
        # Harmonics for texture
        val += 0.2 * math.sin(2 * math.pi * freq * 2 * t)
        val += 0.1 * math.sin(2 * math.pi * freq * 3 * t)
        # Rhythmic pulse (3 Hz amplitude modulation)
        val *= 0.5 + 0.5 * math.sin(2 * math.pi * 3 * t)
        # Fade in/out
        env = min(t * 4, 1.0) * min((duration - t) * 4, 1.0)
        samples.append(int(val * env * 32767))

    data_size = n * 2
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sample_rate,
        sample_rate * 2,
        2,
        16,
        b"data",
        data_size,
    )
    return header + struct.pack(f"<{n}h", *samples)


# Cache the WAV so it's only generated once
_demo_wav = generate_demo_wav()


@element("waveform-editor", height="220px", skeleton=True, imports={"peaks": "https://esm.sh/peaks.js@3"})
def WaveformEditor():
    """Audio waveform viewer with transport controls via Peaks.js."""
    return Div(
        (is_loading := Local("is_loading", True, type_=bool)),
        Local("is_playing", False, type_=bool),
        Local("current_time", 0, type_=float),
        Script("""
            const Peaks = peaks?.default || peaks;
            let peaksInstance = null;
            let blobUrl = null;

            const container = refs('overview');
            const audio = refs('audio');
            const playBtn = refs('play_btn');
            const src = el.getAttribute('src');

            if (!container || !audio || !Peaks || !src) {
                console.error('[WaveformEditor] Missing deps or src attribute');
                $$is_loading = false;
                return;
            }

            // Peaks.js bug: _mouseDown registers mouseup/touchend on window
            // with {passive:true}, then _mouseUp calls preventDefault().
            // Patch window.addEventListener to force passive:false for these events.
            const _origWindowAEL = window.addEventListener;
            const patchEvents = new Set([
                'mouseup', 'mousedown', 'mousemove',
                'touchstart', 'touchmove', 'touchend', 'wheel',
            ]);
            window.addEventListener = function(type, fn, opts) {
                if (patchEvents.has(type)) {
                    if (typeof opts === 'object' && opts !== null) opts = { ...opts, passive: false };
                    else opts = { capture: !!opts, passive: false };
                }
                return _origWindowAEL.call(this, type, fn, opts);
            };

            playBtn.addEventListener('click', () => {
                if (audio.paused) audio.play();
                else audio.pause();
            });

            audio.addEventListener('timeupdate', () => {
                $$current_time = audio.currentTime;
            });

            // Load audio as blob URL so the browser has the full file in memory.
            // Without this, setting audio.currentTime fails because the server
            // response doesn't support HTTP range requests for seeking.
            fetch(src).then(r => r.blob()).then(blob => {
                blobUrl = URL.createObjectURL(blob);
                audio.src = blobUrl;

                Peaks.init({
                    overview: {
                        container,
                        waveformColor: '#7c6ef6',
                        playedWaveformColor: '#a599ff',
                        axisLabelColor: '#6b6b80',
                        axisGridlineColor: '#2a2a3a',
                    },
                    playheadColor: '#e0e0e6',
                    playheadTextColor: '#e0e0e6',
                    mediaElement: audio,
                    webAudio: { audioContext: new AudioContext() },
                }, (err, instance) => {
                    if (err) {
                        console.error('[WaveformEditor] Init error:', err);
                        $$is_loading = false;
                        return;
                    }
                    peaksInstance = instance;
                    $$is_loading = false;
                });
            });

            onCleanup(() => {
                if (peaksInstance) {
                    peaksInstance.destroy();
                    peaksInstance = null;
                }
                if (blobUrl) URL.revokeObjectURL(blobUrl);
                window.addEventListener = _origWindowAEL;
            });
        """),
        Div(
            Div(
                Div(cls="loading-spinner"),
                Span("Analyzing waveform...", cls="loading-text"),
                cls="loading-inner",
            ),
            data_show=is_loading,
            cls="loading-overlay",
        ),
        Div(data_ref="overview", cls="waveform-container"),
        Audio(
            data_ref="audio",
            preload="auto",
            crossorigin="anonymous",
            data_on_play="$$is_playing = true",
            data_on_pause="$$is_playing = false",
            style="display:none;",
        ),
        Div(
            Button(
                data_text="$$is_playing ? '\u23f8' : '\u25b6'",
                data_ref="play_btn",
                cls="transport-btn",
            ),
            Span(data_text="$$current_time.toFixed(1) + 's'", cls="time-display"),
            cls="transport-bar",
        ),
        cls="waveform-editor-root",
    )


app, rt = star_app()
app.register(WaveformEditor)


@rt("/audio/demo")
def audio_demo():
    return Response(_demo_wav, media_type="audio/wav")


@rt("/")
def home():
    return Div(
        Style("""
            *, *::before, *::after { box-sizing: border-box; }

            body {
                margin: 0;
                background: #0f0f13;
                color: #e0e0e6;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                             'Helvetica Neue', Arial, sans-serif;
                -webkit-font-smoothing: antialiased;
            }

            .page-wrapper {
                max-width: 640px;
                margin: 0 auto;
                padding: 3rem 1.5rem;
            }

            .page-header { margin-bottom: 2rem; }

            .page-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: #ffffff;
                margin: 0 0 0.35rem 0;
                letter-spacing: -0.02em;
            }

            .page-subtitle {
                font-size: 0.85rem;
                color: #6b6b80;
                margin: 0;
            }

            .waveform-editor-root {
                position: relative;
                background: #1a1a24;
                border: 1px solid #2a2a3a;
                border-radius: 12px;
                overflow: hidden;
            }

            .loading-overlay {
                position: absolute;
                inset: 0;
                z-index: 10;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #1a1a24;
            }

            .loading-inner {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1rem;
            }

            .loading-spinner {
                width: 28px;
                height: 28px;
                border: 2.5px solid #2a2a3a;
                border-top-color: #7c6ef6;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }

            @keyframes spin { to { transform: rotate(360deg); } }

            .loading-text {
                font-size: 0.8rem;
                color: #6b6b80;
                letter-spacing: 0.03em;
                text-transform: uppercase;
                font-weight: 500;
            }

            .waveform-container {
                background: linear-gradient(180deg, #12121a 0%, #181824 100%);
                min-height: 148px;
                border-bottom: 1px solid #2a2a3a;
                touch-action: none;
            }

            .transport-bar {
                display: flex;
                align-items: center;
                gap: 0.875rem;
                padding: 0.75rem 1rem;
                background: #16161f;
            }

            .transport-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 40px;
                height: 40px;
                border: none;
                border-radius: 50%;
                background: #7c6ef6;
                color: #fff;
                font-size: 1.1rem;
                cursor: pointer;
                transition: background 0.15s ease, transform 0.1s ease;
                flex-shrink: 0;
                line-height: 1;
                padding: 0;
            }

            .transport-btn:hover { background: #9084f7; }
            .transport-btn:active { transform: scale(0.93); background: #6a5cd4; }

            .time-display {
                font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
                font-size: 0.95rem;
                font-weight: 500;
                color: #a0a0b8;
                letter-spacing: 0.04em;
                min-width: 5em;
            }
        """),
        Div(
            Div(
                H1("Waveform Editor", cls="page-title"),
                P("Peaks.js audio visualization with transport controls.", cls="page-subtitle"),
                cls="page-header",
            ),
            WaveformEditor(src="/audio/demo"),
            cls="page-wrapper",
        ),
    )


if __name__ == "__main__":
    serve()
