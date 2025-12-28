"""Example: Waveform editor component using starelements with Peaks.js."""

from starhtml import Div, Canvas, Button, Span
from starelements import element


@element("waveform-editor")
class WaveformEditor:
    """
    Audio waveform editor with clip selection.

    Demonstrates:
    - External library imports (Peaks.js)
    - Setup script for initialization
    - Event handling and cleanup
    """

    # External library imports
    imports = {
        "Peaks": "https://esm.sh/peaks.js@3"
    }

    def render(self):
        """Render the component template."""
        return Div(
            Div("Loading waveform...", data_show="$isLoading", cls="loading"),
            Canvas(data_ref="waveform", style="width:100%;height:128px;"),
            Div(
                Button(data_text="$isPlaying ? '⏸' : '▶'", data_on_click="@togglePlay()"),
                Span(data_text="$currentTime.toFixed(2) + 's'"),
                style="display:flex;gap:1rem;margin-top:0.5rem;",
            ),
        )

    def setup(self) -> str:
        """Setup script - runs when component is connected."""
        return '''
            // Local signals
            $isLoading = true;
            $isPlaying = false;
            $currentTime = 0;

            // Define actions
            actions.togglePlay = () => {
                $isPlaying = !$isPlaying;
                if ($isPlaying) {
                    this.peaks?.player.play();
                } else {
                    this.peaks?.player.pause();
                }
            };

            // Initialize Peaks.js when canvas is ready
            effect(() => {
                if (!$waveform || !Peaks) return;
                if (this.peaks) return;

                const peaksUrl = el.getAttribute('peaks-url');
                if (!peaksUrl) return;

                Peaks.init({
                    container: $waveform,
                    mediaElement: document.createElement('audio'),
                    dataUri: { json: peaksUrl },
                    height: 128,
                }).then(peaks => {
                    this.peaks = peaks;
                    $isLoading = false;

                    peaks.on('player.timeupdate', (time) => {
                        $currentTime = time;
                    });
                }).catch(err => {
                    console.error('Peaks init error:', err);
                    $isLoading = false;
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
    from fastcore.xml import to_xml
    from starelements.generator import generate_template_ft

    # Show generated template
    ft = generate_template_ft(WaveformEditor._element_def, WaveformEditor)
    print("=== Template ===")
    print(to_xml(ft))

    # Show usage example
    print("\n=== Usage Example ===")
    print(WaveformEditor(peaks_url="/api/peaks/example.json"))
