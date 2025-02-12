# Test the model
import torch
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

def test_results(model, X, y, output_class, output_dir):
    model.load_state_dict(torch.load(f"{output_dir}/pytorch_model_best.pth", weights_only=False)) 
    model.eval()
    X_test_tensor = torch.tensor(X, dtype=torch.float32)
    
    with torch.no_grad():
        outputs_test = model(X_test_tensor)
        
        match output_class:
            case "binary":
                predictions = torch.sigmoid(outputs_test).cpu().numpy()

    fpr, tpr, threshold = roc_curve(y[:, 1], predictions[:, 1])

    # Plot ROC curve
    plt.figure()
    plt.plot(tpr, fpr, lw=2.5, label="AUC = {:.1f}%".format(auc(fpr, tpr) * 100))
    plt.xlabel(r'True positive rate')
    plt.ylabel(r'False positive rate')
    plt.semilogy()  # Log scale on the y-axis
    plt.ylim(0.001, 1)
    plt.xlim(0, 1)
    plt.grid(True)
    plt.legend(loc='upper left')
    plt.tight_layout()

    plt.savefig(f'{output_dir}/ROC.png')
    plt.savefig(f'{output_dir}/ROC.pdf')

    return 0
