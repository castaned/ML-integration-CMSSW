# Test the model
import torch
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
import models.models as mdls

def test_results(X, y, output_class, output_dir):
    
    param_model = torch.load(f"{output_dir}/pytorch_best_model.pth", weights_only=True)
    hyperparam = param_model["hyperparam"]
    model = mdls.MLPmodel(
                  input_size=X.shape[1],
                  output_size=y.shape[1],
                  hidden_input_size=hyperparam["hidden_input_size"],
                  hidden_output_size=hyperparam["hidden_output_size"],
                  num_layers=hyperparam["num_layers"]
                  )

    model.load_state_dict(param_model["model_state"])
    print(model)
    
    model.eval()
    X_test_tensor = torch.tensor(X, dtype=torch.float32)
    
    with torch.no_grad():
        outputs_test = model(X_test_tensor)
        
        if output_class == "binary":
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
