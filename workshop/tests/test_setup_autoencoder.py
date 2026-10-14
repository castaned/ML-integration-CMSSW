import sys
from pathlib import Path
import tempfile
import unittest
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from setup_autoencoder import generate


class ConfigTests(unittest.TestCase):
    def test_shared_inputs_preserved_and_personal_results(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            normal, signal = temp / 'shared_sm', temp / 'shared_signal'
            normal.mkdir(); signal.mkdir()
            config = {'data': {'normal_input_paths': [str(normal)], 'anomaly_input_paths': [str(signal)],
                       'features': ['MET_pt'], 'output_path': 'instructor_results'},
                       'model': {'name': 'original', 'export_onnx': True}}
            source = temp / 'source.yaml'
            source.write_text(yaml.safe_dump(config))
            generate(source, temp / 'student.yaml', temp / 'student_results')
            student = yaml.safe_load((temp / 'student.yaml').read_text())
            self.assertEqual(student['data']['normal_input_paths'], [str(normal.resolve())])
            self.assertEqual(student['data']['output_path'], str((temp / 'student_results').resolve()))
            self.assertEqual(yaml.safe_load(source.read_text()), config)
            self.assertFalse(student['model']['export_onnx'])
            with self.assertRaises(FileExistsError): generate(source, temp / 'student.yaml', temp / 'student_results')


if __name__ == '__main__': unittest.main()
