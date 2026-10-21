"""Benchmark API endpoint — PRD §8.2."""

from fastapi import APIRouter

from chaukas.bench.runner import run_benchmark

router = APIRouter()


@router.post("/benchmark")
async def benchmark(req: dict):
    """Run benchmark on the corpus with optional ASR noise."""
    noise_wer = req.get("noise_wer", 0.0)
    sensitivity = req.get("sensitivity", "standard")
    danger_threshold = req.get("danger_threshold")
    seed = req.get("seed")

    result = run_benchmark(
        noise_wer=noise_wer,
        sensitivity=sensitivity,
        danger_threshold=danger_threshold,
        seed=seed,
    )
    return result