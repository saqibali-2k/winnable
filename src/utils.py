import numpy as np
import pickle


def load_dataset(dataset_path, dataset_labels_path) -> tuple[np.ndarray, np.ndarray]:
    X = np.load(dataset_path)
    y = np.load(dataset_labels_path)
    if isinstance(X, np.ndarray) and isinstance(y, np.ndarray):
        return X, y
    else:
        raise ValueError


def save_dataset(X, y, dataset_path, dataset_labels_path):
    np.save(X, dataset_path)
    np.save(y, dataset_labels_path)


def load_model(model_path):
    with open(model_path, "rb") as f:
        return pickle.load(f)


def save_model(model, model_path):
    with open(model_path, "wb") as f:
        return pickle.dump(model, f)


def shuffle_X_y(X: np.ndarray, y: np.ndarray):
    """
    Randomly shuffles the rows of the 2D feature matrix X and the corresponding 1D label vector y.

    Parameters:
    X (np.ndarray): 2D array of shape (num_samples, num_features), the feature matrix.
    y (np.ndarray): 1D array of shape (num_samples,), the corresponding label vector.

    Returns:
    X_shuffled (np.ndarray): Shuffled 2D feature matrix.
    y_shuffled (np.ndarray): Shuffled 1D label vector.
    """
    assert len(X) == len(y), "The number of samples in X and y must be the same."

    # Generate a permutation of indices
    indices = np.random.permutation(len(X))

    # Shuffle X and y using the generated indices
    X_shuffled = X[indices]
    y_shuffled = y[indices]

    return X_shuffled, y_shuffled


def split_train_validation(X: np.ndarray, y: np.ndarray, validation_size: float = 0.2):
    """
    Splits the dataset into training and validation sets with 80-20 split by default.

    Parameters:
    X (np.ndarray): 2D array of shape (num_samples, num_features), the feature matrix.
    y (np.ndarray): 1D array of shape (num_samples,), the corresponding label vector.
    validation_size (float): Proportion of the dataset to include in the validation split (default is 0.2, i.e., 20%).

    Returns:
    X_train (np.ndarray): Training set features.
    y_train (np.ndarray): Training set labels.
    X_val (np.ndarray): Validation set features.
    y_val (np.ndarray): Validation set labels.
    """
    assert len(X) == len(y), "The number of samples in X and y must be the same."

    # Generate a permutation of indices to shuffle the dataset
    indices = np.random.permutation(len(X))

    # Determine the split index
    split_index = int(len(X) * (1 - validation_size))

    # Split the indices into training and validation indices
    train_indices = indices[:split_index]
    val_indices = indices[split_index:]

    # Split X and y into training and validation sets
    X_train, X_val = X[train_indices], X[val_indices]
    y_train, y_val = y[train_indices], y[val_indices]

    return X_train, X_val, y_train, y_val
