import onnxruntime as ort
import uproot
import numpy as np

# Load ONNX model
model_path = "my_model.onnx"
session = ort.InferenceSession(model_path)

# Get input details
input_name = session.get_inputs()[0].name
input_shape = session.get_inputs()[0].shape
input_type = session.get_inputs()[0].type

print(f"Model expects input: {input_name}, shape: {input_shape}, type: {input_type}")

# Open NanoAOD file
nanoAOD_file = "myNanoAOD.root"
tree_name = "Events"

with uproot.open(nanoAOD_file)[tree_name] as tree:
    # List available branches (useful for debugging)
    print("Available branches:", tree.keys())

    # Select branches to use as model inputs (adjust as needed)
    branches = ["Electron_pt", "Electron_eta", "Electron_phi", "Electron_mass"]

    # Load event data
    data = tree.arrays(branches, library="np")

    # Loop over events
    for i in range(len(data["Electron_pt"])):
        # Check if event has electrons
        if len(data["Electron_pt"][i]) == 0:
            continue  # Skip empty events

        # Example: Take first electron in the event
        pt = data["Electron_pt"][i][0]
        eta = data["Electron_eta"][i][0]
        phi = data["Electron_phi"][i][0]
        mass = data["Electron_mass"][i][0]

        # Convert event data into model input format
        input_data = np.array([[pt, eta, phi, mass]], dtype=np.float32)

        # Run inference
        output = session.run(None, {input_name: input_data})

        # Print results
        print(f"Event {i}, Electron pt={pt:.2f}, Model Output={output}")

print("Processing completed!")
