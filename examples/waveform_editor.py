"""Example: Waveform editor component using starelements."""

from starelements import element, prop, signal


@element("waveform-editor")
class WaveformEditor:
    """
    Audio waveform editor with clip selection.

    Props:
        peaks_url: URL to peaks data file
        clip_start: Start time of clip (seconds)
        clip_end: End time of clip (seconds)

    Events:
        change: Fired when clip bounds change {start: float, end: float}
        seek: Fired when playhead position changes (float)
    """

    # Props - observed attributes with validation
    peaks_url: str = prop(required=True)
    clip_start: float = prop(default=0.0, ge=0)
    clip_end: float = prop(default=0.0, ge=0)

    # Internal signals - scoped to instance
    is_playing: bool = signal(False)
    current_time: float = signal(0.0)
    is_loading: bool = signal(True)

    # External library imports
    imports = {
        "Peaks": "https://esm.sh/peaks.js@3"
    }

    # Events this component emits
    class Events:
        change: dict  # {start: float, end: float}
        seek: float

    def render(self):
        """Render the component template."""
        return """
        <div class="waveform-editor">
            <!-- Loading indicator -->
            <div data-show="$is_loading" class="loading-indicator">
                <span>Loading waveform...</span>
            </div>

            <!-- Waveform canvas -->
            <canvas data-ref="waveform" class="waveform-canvas w-full h-32"></canvas>

            <!-- Controls -->
            <div class="controls flex gap-2 mt-2">
                <button data-text="$is_playing ? '⏸' : '▶'" data-on:click="@togglePlay()" class="play-btn"></button>
                <div class="time-controls">
                    <input type="number" step="0.001" data-bind="$clip_start" class="time-input">
                    <span>→</span>
                    <input type="number" step="0.001" data-bind="$clip_end" class="time-input">
                </div>
            </div>
        </div>
        """

    def setup(self) -> str:
        """Setup script - runs when component is connected."""
        return '''
            // Define actions
            actions.togglePlay = () => {
                $is_playing = !$is_playing;
                if ($is_playing) {
                    this.peaks?.player.play();
                } else {
                    this.peaks?.player.pause();
                }
            };

            // Initialize Peaks.js when canvas is ready
            effect(() => {
                if (!$waveform || !Peaks) return;
                if (this.peaks) return; // Already initialized

                const peaksUrl = el.getAttribute('peaks-url');
                if (!peaksUrl) return;

                Peaks.init({
                    container: $waveform,
                    mediaElement: document.createElement('audio'),
                    dataUri: { json: peaksUrl },
                    height: 128,
                    waveformColor: 'rgba(212, 165, 68, 0.6)',
                    playedWaveformColor: 'rgba(212, 165, 68, 1)',
                    pointMarkerColor: '#d4a544',
                    segments: [{
                        startTime: $clip_start,
                        endTime: $clip_end,
                        color: 'rgba(212, 165, 68, 0.3)',
                        editable: true
                    }]
                }).then(peaks => {
                    this.peaks = peaks;
                    $is_loading = false;

                    // Listen for segment changes
                    peaks.on('segments.dragged', (segment) => {
                        $clip_start = segment.startTime;
                        $clip_end = segment.endTime;
                        el.emit('change', {
                            start: segment.startTime,
                            end: segment.endTime
                        });
                    });

                    // Track playback position
                    peaks.on('player.timeupdate', (time) => {
                        $current_time = time;
                    });
                }).catch(err => {
                    console.error('Peaks init error:', err);
                    $is_loading = false;
                });
            });

            // Cleanup
            onCleanup(() => {
                if (this.peaks) {
                    this.peaks.destroy();
                    this.peaks = null;
                }
            });
        '''


if __name__ == "__main__":
    from starelements import starelements_head, get_component_assets

    # Show generated template
    assets = get_component_assets(WaveformEditor)
    print("=== Template ===")
    print(assets["template"])
    print("\n=== Script ===")
    print(assets["script"])

    # Show usage example
    print("\n=== Usage Example ===")
    instance = WaveformEditor(
        peaks_url="/api/peaks/example.json",
        clip_start="$clip_start",
        clip_end="$clip_end",
        on_change="$clip_start = evt.detail.start; $clip_end = evt.detail.end"
    )
    print(str(instance))
