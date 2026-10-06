"""Compare 1/4-thread caches byte-for-byte; record the allowed accuracy budget."""
import json
from pathlib import Path
root = Path('/work/data/phase-3/determinism')
checks = {model: (root / f'{model}-1.txt').read_bytes() == (root / f'{model}-4.txt').read_bytes()
          for model in ('nano', 'tiny')}
result = {'sequence': 'MOT17-02-FRCNN', 'frames': [1, 50],
          'bit_identical': checks, 'accuracy_threads': 4 if all(checks.values()) else 1}
Path('/work/results/phase-3/thread-determinism.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result), flush=True)
