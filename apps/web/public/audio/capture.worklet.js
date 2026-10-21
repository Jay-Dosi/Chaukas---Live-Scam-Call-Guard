// AudioWorklet processor for 16kHz mono PCM16 capture
// Runs on audio thread, no main thread blocking

class PcmProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Float32Array(1600); // 100ms at 16kHz
    this.bufferIndex = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;

    const channel = input[0]; // mono
    if (!channel) return true;

    for (let i = 0; i < channel.length; i++) {
      // Convert float32 [-1, 1] to int16
      const sample = Math.max(-1, Math.min(1, channel[i]));
      const int16 = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;

      this.buffer[this.bufferIndex++] = int16;

      if (this.bufferIndex >= this.buffer.length) {
        // Convert to Int16Array and send
        const int16Buffer = new Int16Array(this.buffer);
        this.port.postMessage({ type: 'pcm', buffer: int16Buffer.buffer }, [int16Buffer.buffer]);
        this.bufferIndex = 0;
      }
    }

    return true;
  }
}

registerProcessor('pcm-processor', PcmProcessor);