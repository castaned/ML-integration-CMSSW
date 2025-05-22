# Test the model
import torch
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
import models.models as mdls
from sklearn.preprocessing import label_binarize
import numpy as np
from itertools import cycle
import utilities.prepare_data as preda

def test_results(X, y, output_class, output_dir, model_name):
    
    param_model = torch.load(f"{output_dir}/best_model_{model_name}_{output_class}.pth", weights_only=True)
    # hyperparam = param_model["hyperparam"]
    # model = mdls.MLPmodel(
    #                input_size=X.shape[1],
    #                output_size=y.shape[1],
    #                hidden_input_size=hyperparam["hidden_input_size"],
    #                hidden_output_size=hyperparam["hidden_output_size"],
    #                num_layers=hyperparam["num_layers"]
    #                )
    # model.load_state_dict(param_model["model_state"])
    if model_name == 'mlp':
        model = mdls.MLPmodel.get_model(X, y, param_model)
    print(model)
    
    model.eval()
    X_test_tensor = torch.tensor(X, dtype=torch.float32)
    
    label_decoder = np.load(f"{output_dir}/label_decoder.npy")
    clean_label_decoder = preda.clean_array_values(label_decoder)
    
    with torch.no_grad():
        outputs_test = model(X_test_tensor)
        
        if output_class == "binary":
            predictions = torch.sigmoid(outputs_test).cpu().numpy()
            fpr, tpr, _ = roc_curve(y[:, 1], predictions[:, 1])
            roc_auc = auc(fpr, tpr)
            
            plt.figure()
            plt.plot(fpr, tpr, lw=2, label=f'AUC = {roc_auc:.2f}')
        elif output_class == "multiclass":
            probabilities = torch.softmax(outputs_test, dim=1).cpu().numpy()
            n_classes = probabilities.shape[1]
            
            # Binarize labels for OvR
            y_true = np.argmax(y, axis=1) if y.ndim > 1 else y
            y_bin = label_binarize(y_true, classes=np.arange(n_classes))
            
            fpr, tpr, roc_auc = dict(), dict(), dict()
            colors = cycle(['blue', 'red', 'green', 'purple', 'orange'])
            
            plt.figure()
            for i, color in zip(range(n_classes), colors):
                fpr[i], tpr[i], _ = roc_curve(y_bin[:, i], probabilities[:, i])
                roc_auc[i] = auc(fpr[i], tpr[i])
                plt.plot(fpr[i], tpr[i], color=color, lw=2,
                         label=f'Label {clean_label_decoder[i]} (AUC = {roc_auc[i]:.2f})')

    # Plot ROC curve
    # plt.figure()
    # plt.plot(tpr, fpr, lw=2.5, label="AUC = {:.1f}%".format(auc(fpr, tpr) * 100))
    # plt.xlabel(r'True positive rate')
    # plt.ylabel(r'False positive rate')
    # plt.semilogy()  # Log scale on the y-axis
    # plt.ylim(0.001, 1)
    # plt.xlim(0, 1)
    # plt.grid(True)
    # plt.legend(loc='upper left')
    # plt.tight_layout()

    plt.plot([0, 1], [0, 1], 'k--', lw=2)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.legend(loc="lower right")
    plt.grid(True)

    plt.savefig(f'{output_dir}/ROC_{model_name}_{output_class}.png')
    plt.savefig(f'{output_dir}/ROC_{model_name}_{output_class}.pdf')
    plt.close()

    return 0
