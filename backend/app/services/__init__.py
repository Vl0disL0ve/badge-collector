from .ml import (
    auto_rotate, 
    rotate_image, 
    remove_background, 
    process_image,
    detect_axis,
    rotate_to_axis,
    rotate_custom,
    detect_badges_on_set,
    center_to_square
)
from .similarity import (
    extract_features,
    find_similar_badges,
    update_all_features,
    get_badge_vector,
    compute_similarity
)

__all__ = [
    # ML functions
    "auto_rotate",
    "rotate_image", 
    "remove_background",
    "process_image",
    "detect_axis",
    "rotate_to_axis",
    "rotate_custom",
    "detect_badges_on_set",
    "center_to_square",
    # Similarity functions
    "extract_features",
    "find_similar_badges",
    "update_all_features",
    "get_badge_vector",
    "compute_similarity"
]