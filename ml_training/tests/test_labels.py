import unittest

from utilities.labels import encode_label, normalize_class_id_map, remap_class_names


class LabelMappingTests(unittest.TestCase):
    def test_signal_and_background_ids(self):
        mapping = normalize_class_id_map({1: 1, 2: 0}, 2)
        self.assertEqual(encode_label(1, 2, mapping), 1)
        self.assertEqual(encode_label(2, 2, mapping), 0)
        self.assertEqual(remap_class_names({1: "senal", 2: "fondo"}, mapping), {1: "senal", 0: "fondo"})

    def test_identity_labels_without_mapping(self):
        self.assertEqual(encode_label(0, 2), 0)
        self.assertEqual(encode_label(1, 2), 1)

    def test_invalid_mapping_or_label_fails(self):
        with self.assertRaises(ValueError):
            normalize_class_id_map({1: 0, 2: 0}, 2)
        with self.assertRaises(ValueError):
            encode_label(2, 2)
        with self.assertRaises(ValueError):
            encode_label(3, 2, {1: 1, 2: 0})


if __name__ == "__main__":
    unittest.main()
