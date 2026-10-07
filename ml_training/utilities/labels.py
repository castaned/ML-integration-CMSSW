def normalize_class_id_map(class_id_map, num_classes):
    if class_id_map is None:
        return None

    normalized = {int(raw): int(index) for raw, index in class_id_map.items()}
    if len(normalized) != num_classes or set(normalized.values()) != set(range(num_classes)):
        raise ValueError("class_id_map must map each raw label to one class index in 0..num_classes-1")
    return normalized


def encode_label(raw_label, num_classes, class_id_map=None):
    raw_label = int(raw_label)
    if class_id_map is not None:
        if raw_label not in class_id_map:
            raise ValueError(f"Dataset label {raw_label} is missing from class_id_map")
        return class_id_map[raw_label]
    if not 0 <= raw_label < num_classes:
        raise ValueError(f"Dataset label {raw_label} is outside model classes 0..{num_classes - 1}; set class_id_map")
    return raw_label


def remap_class_names(class_names, class_id_map):
    if class_id_map is None:
        return class_names
    return {class_id_map[raw]: name for raw, name in class_names.items()}
