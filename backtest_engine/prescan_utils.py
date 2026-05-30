import logging
import math
import numpy as np

logger = logging.getLogger(__name__)

def downsample_parameter_grid(
    arrays_to_downsample: dict[str, list],
    max_combos: int = 20000,
    strategy_name: str = "Unknown"
) -> dict[str, list]:
    """
    Uniformly downsamples a set of parameter arrays so that their cartesian product
    size does not exceed max_combos. It preserves the boundaries (first and last elements).
    
    Args:
        arrays_to_downsample: dict mapping parameter name to a sorted list of unique values.
        max_combos: Maximum allowed combinations.
        strategy_name: Name used in logging.
        
    Returns:
        dict of downsampled arrays (same keys as input).
    """
    total_combos = math.prod(len(v) for v in arrays_to_downsample.values())
    
    if total_combos <= max_combos:
        return arrays_to_downsample
        
    logger.warning(
        f"{strategy_name} pre-scan: {total_combos} combinaisons > {max_combos}, "
        "sous-echantillonnage applique (grille reduite)."
    )
    
    num_dims = len(arrays_to_downsample)
    if num_dims == 0:
        return arrays_to_downsample
        
    ratio = (total_combos / float(max_combos)) ** (1.0 / num_dims)
    
    def subsample_array(arr: list, target_len: int) -> list:
        if len(arr) <= target_len:
            return arr
        indices = np.linspace(0, len(arr) - 1, target_len).astype(int)
        return sorted(list({arr[i] for i in indices}))
        
    downsampled = {}
    for name, arr in arrays_to_downsample.items():
        target_len = max(2, int(len(arr) / ratio))
        downsampled[name] = subsample_array(arr, target_len)
        
    return downsampled
