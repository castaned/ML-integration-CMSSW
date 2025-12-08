import torch
import onnx
import onnxruntime as ort
from torch.utils.data import DataLoader
import numpy as np

def compute_accuracy(outputs, y):
    _, predicted = torch.max(outputs, dim=1)
    correct = (predicted == y).sum().item()
    total = y.size(0)
    acc = correct/total
    return acc

def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

def convert_to_onnx(input_dim, model, output_dir, model_name, opset=12):

    dummy_input = torch.randn(1, input_dim, dtype=torch.float32)

    model.eval()
    torch.onnx.export(
        model,
        dummy_input,
        f"{output_dir}/best_model_{model_name}.onnx",
        export_params=True,
        opset_version=opset,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }
    )
    
    # Verify
    onnx.checker.check_model(onnx.load(f"{output_dir}/best_model_{model_name}.onnx"))
    return 0

def onnx_inference(onnx_path, dataset, batch_size=2048):

    ort_session = ort.InferenceSession(onnx_path)
    input_name = ort_session.get_inputs()[0].name
    
    dataloader = DataLoader(dataset, batch_size=batch_size)
    
    predictions_all = []
    probabilities_all = []
    
    for batch in dataloader:
        
        if isinstance(batch, tuple) or isinstance(batch, list):
            X_batch = batch[0]
        else:
            X_batch = batch
            
        outputs = ort_session.run(None, {input_name: X_batch.cpu().numpy().astype(np.float32)})[0]
        
        probabilities = torch.softmax(torch.tensor(outputs, dtype=torch.float32), dim=1).numpy()
        predictions = np.argmax(probabilities, axis=1)
        
    predictions_all.append(predictions)
    probabilities_all.append(probabilities)
    
    predictions_all = np.concatenate(predictions_all)
    probabilities_all = np.concatenate(probabilities_all)
    
    return predictions_all, probabilities_all
