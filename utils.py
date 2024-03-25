import numpy as np
import pickle


def load_dataset(dataset_path, dataset_labels_path):
    X = np.load(dataset_path)
    y = np.load(dataset_labels_path)

    return X, y


def save_dataset(X, y, dataset_path, dataset_labels_path):
    np.save(X, dataset_path)
    np.save(y, dataset_labels_path)


def load_model(model_path):
    return pickle.load(model_path)


def save_model(model, model_path):
    pickle.dump(model, model_path)




