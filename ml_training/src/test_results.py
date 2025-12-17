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

def compute_ROC(outputs, labels, num_classes, output_dir, model_name, class_labels=None):
        
    if class_labels is None:
        class_labels = {i: f'Label {i}' for i in range(num_classes)}

    if num_classes == 2: # Binary
        probabilities = torch.softmax(torch.tensor(outputs, dtype=torch.float32), dim=1)[:, 1].numpy()
        fpr, tpr, _ = roc_curve(labels, probabilities)
        roc_auc = auc(fpr, tpr)

        label_name = class_labels.get(1, f'Label 1')
        plt.plot(fpr, tpr, lw=2, label=f'{label_name} AUC = {roc_auc:.2f}')
    else: # Multiclass
        probabilities = torch.softmax(torch.tensor(outputs, dtype=torch.float32), dim=1).numpy()
        n_classes = probabilities.shape[1]
        
        y_bin = label_binarize(labels, classes=np.arange(n_classes))
            
        fpr, tpr, roc_auc = dict(), dict(), dict()
        colors = cycle(['blue', 'red', 'green', 'purple', 'orange'])
        
        for i, color in zip(range(n_classes), colors):
            fpr[i], tpr[i], _ = roc_curve(y_bin[:, i], probabilities[:, i])
            roc_auc[i] = auc(fpr[i], tpr[i])

            label_name = class_labels.get(i, f'Label {i}')
            plt.plot(fpr[i], tpr[i], color=color, lw=2,
                     label=f'{label_name} (AUC = {roc_auc[i]:.2f})')
                
                
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

def compute_cm(outputs, labels, output_dir, model_name, class_labels=None):
    
    predictions = np.argmax(outputs, axis=1)
    
    cm = confusion_matrix(labels, predictions)

    if isinstance(class_labels, dict): 
        label_names = [class_labels.get(i, str(i)) for i in range(len(class_labels))] 
    else: 
        label_names = [str(i) for i in range(cm.shape[0])]

    n_classes = len(label_names)
    plt.figure(figsize=(max(8, n_classes * 0.8), max(6, n_classes * 0.7)))

    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=label_names)
    disp.plot(cmap="Blues", values_format="d", xticks_rotation=45 if n_classes > 2 else 0)

    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/cm_{model_name}.png", dpi=200, bbox_inches='tight')
    plt.savefig(f"{output_dir}/cm_{model_name}.pdf", dpi=200, bbox_inches='tight')
    plt.close()
    
    return 0

def test_results(model_name, model_type, dataset, output_dir, batch_size=2048, class_labels=None):
    
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
    
    compute_ROC(outputs_test, labels_test, dataset.num_classes, output_dir, model_name, class_labels)
    compute_cm(outputs_test, labels_test, output_dir, model_name, class_labels)

    dataset.close()
    return 0
