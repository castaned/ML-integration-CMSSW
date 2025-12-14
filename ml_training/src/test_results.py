# Test the model
import torch
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
import models.models as models
from sklearn.preprocessing import label_binarize
import numpy as np
from itertools import cycle
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

def compute_ROC(outputs, labels, num_classes, output_dir, model_name):

        if num_classes == 2: # Binary
            probabilities = torch.softmax(torch.tensor(outputs, dtype=torch.float32), dim=1)[:, 1].numpy()
            fpr, tpr, _ = roc_curve(labels, probabilities)
            roc_auc = auc(fpr, tpr)
            
            plt.plot(fpr, tpr, lw=2, label=f'AUC = {roc_auc:.2f}')
        else: # Multiclass
            probabilities = torch.softmax(torch.tensor(outputs, dtype=torch.float32), dim=1).numpy()
            n_classes = probabilities.shape[1]
            
            y_bin = label_binarize(labels, classes=np.arange(n_classes))
            
            fpr, tpr, roc_auc = dict(), dict(), dict()
            colors = cycle(['blue', 'red', 'green', 'purple', 'orange'])
            
            for i, color in zip(range(n_classes), colors):
                fpr[i], tpr[i], _ = roc_curve(y_bin[:, i], probabilities[:, i])
                roc_auc[i] = auc(fpr[i], tpr[i])
                plt.plot(fpr[i], tpr[i], color=color, lw=2,
                         label=f'Label {i} (AUC = {roc_auc[i]:.2f})')
                
                
        plt.plot([0, 1], [0, 1], 'k--', lw=2)
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve')
        plt.legend(loc="lower right")
        plt.grid(True)
        
        plt.savefig(f'{output_dir}/ROC_{model_name}.png')
        plt.savefig(f'{output_dir}/ROC_{model_name}.pdf')
        plt.close()
        
        return 0

def compute_cm(outputs, labels, output_dir, model_name):
    
    predictions = np.argmax(outputs, axis=1)
    
    cm = confusion_matrix(labels, predictions)
    
    plt.figure(figsize=(7, 7))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap="Blues", values_format="d")
    plt.title("Confusion Matrix")
    plt.savefig(f"{output_dir}/cm_{model_name}.png", dpi=200, bbox_inches='tight')
    plt.savefig(f"{output_dir}/cm_{model_name}.pdf", dpi=200, bbox_inches='tight')
    plt.close()
    
    return 0

def test_results(model_name, model_type, dataset, output_dir, batch_size=2048):
    
    param_model = torch.load(f"{output_dir}/best_model_{model_name}.pth", weights_only=True)
    
    if model_type == 'mlp':
        model = models.MLPmodel.get_model(dataset.num_features, dataset.num_classes, param_model)
    print(model)
    
    dataloader = DataLoader(dataset, batch_size=batch_size)
    
    
    all_outputs = []
    all_labels = []
    
    model.eval()
    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            outputs = model(X_batch)
            
            all_outputs.append(outputs.cpu().numpy())
            all_labels.append(y_batch.cpu().numpy())
            
    outputs_test = np.concatenate(all_outputs)
    labels_test = np.concatenate(all_labels)
    
    compute_ROC(outputs_test, labels_test, dataset.num_classes, output_dir, model_name)
    compute_cm(outputs_test, labels_test, output_dir, model_name)

    dataset.close()
    return 0
