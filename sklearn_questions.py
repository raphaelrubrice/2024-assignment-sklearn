"""Assignment - making a sklearn estimator and cv splitter.

The goal of this assignment is to implement by yourself:

- a scikit-learn estimator for the KNearestNeighbors for classification
  tasks and check that it is working properly.
- a scikit-learn CV splitter where the splits are based on a Pandas
  DateTimeIndex.

Detailed instructions for question 1:
The nearest neighbor classifier predicts for a point X_i the target y_k of
the training sample X_k which is the closest to X_i. We measure proximity with
the Euclidean distance. The model will be evaluated with the accuracy (average
number of samples corectly classified). You need to implement the `fit`,
`predict` and `score` methods for this class. The code you write should pass
the test we implemented. You can run the tests by calling at the root of the
repo `pytest test_sklearn_questions.py`. Note that to be fully valid, a
scikit-learn estimator needs to check that the input given to `fit` and
`predict` are correct using the `check_*` functions imported in the file.
You can find more information on how they should be used in the following doc:
https://scikit-learn.org/stable/developers/develop.html#rolling-your-own-estimator.
Make sure to use them to pass `test_nearest_neighbor_check_estimator`.


Detailed instructions for question 2:
The data to split should contain the index or one column in
datatime format. Then the aim is to split the data between train and test
sets when for each pair of successive months, we learn on the first and
predict of the following. For example if you have data distributed from
november 2020 to march 2021, you have have 4 splits. The first split
will allow to learn on november data and predict on december data, the
second split to learn december and predict on january etc.

We also ask you to respect the pep8 convention: https://pep8.org. This will be
enforced with `flake8`. You can check that there is no flake8 errors by
calling `flake8` at the root of the repo.

Finally, you need to write docstrings for the methods you code and for the
class. The docstring will be checked using `pydocstyle` that you can also
call at the root of the repo.

Hints
-----
- You can use the function:

from sklearn.metrics.pairwise import pairwise_distances

to compute distances between 2 sets of samples.
"""
import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator
from sklearn.base import ClassifierMixin

from sklearn.model_selection import BaseCrossValidator

from sklearn.utils.validation import check_X_y, check_is_fitted, validate_data
from sklearn.utils.validation import check_array
from sklearn.utils.multiclass import check_classification_targets


class KNearestNeighbors(ClassifierMixin, BaseEstimator):
    """KNearestNeighbors classifier."""

    def __init__(self, n_neighbors=1):  # noqa: D107
        self.n_neighbors = n_neighbors

    def fit(self, X, y):
        """Fitting function.

         Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)
            Data to train the model.
        y : ndarray, shape (n_samples,)
            Labels associated with the training data.

        Returns
        ----------
        self : instance of KNearestNeighbors
            The current instance of the classifier
        """
        X = check_array(X)
        check_classification_targets(y)
        X, y = check_X_y(X, y)
        X, y = validate_data(self, X, y)
        self.n_features_in_ = X.shape[1]
        self.is_fitted_ = True
        self.examples_ = X
        self.labels_ = y
        self.classes_ = list(np.unique(y))
        return self

    def euclidian_distance(self, x1, x2, axis=1):
        """Compute euclidian distance for one example.

        Parameters
        ----------
        x1 : ndarray, shape (1, n_features)
        x2 : ndarray, shape (1, n_features)
        Returns
        ----------
        distance : np.float
            distances between x1 and x2.
        """
        return np.sqrt(np.sum((x1 - x2)**2, axis=axis))

    def compute_distance(self, x):
        """Compute all euclidian distances for one example.

        Parameters
        ----------
        x : ndarray, shape (1, n_features)
            Data to predict on.

        Returns
        ----------
        distance : ndarray, shape (1, n_train_samples)
            distances between x and each fitted data point.
        """
        return self.euclidian_distance(self.examples_,
                                       x.reshape(1, -1)).reshape(1, -1)

    def predict(self, X):
        """Predict function.

        Parameters
        ----------
        X : ndarray, shape (n_test_samples, n_features)
            Data to predict on.

        Returns
        ----------
        y : ndarray, shape (n_test_samples,)
            Predicted class labels for each test data sample.
        """
        check_is_fitted(self)
        X = check_array(X)
        X = validate_data(self, X, reset=False)
        y_pred = np.zeros(X.shape[0], dtype=type(self.labels_[0]))
        # Computes distances between each test_datapoint and known datapoints
        distance_matrix = np.zeros((X.shape[0], self.examples_.shape[0]))
        for test_i in range(X.shape[0]):
            distance_matrix[test_i, :] = self.compute_distance(X[test_i, :])
        # Finds the n_neighbors nearest points to our each test_example
        NEIGHBORS = []
        MAX = np.max(distance_matrix)
        for neighbor in range(self.n_neighbors):
            NEIGHBORS.append(np.argmin(distance_matrix, axis=1))
            for row in range(distance_matrix.shape[0]):
                min_pos = NEIGHBORS[-1][row]
                distance_matrix[row, min_pos] = MAX
        # Find label for each test_example
        for test_example in range(X.shape[0]):
            counts = [0]*len(self.classes_)
            for neighbor in range(self.n_neighbors):
                i = NEIGHBORS[neighbor][test_example]
                neighbor_label = self.labels_[i]
                counts[self.classes_.index(neighbor_label)] += 1
            y_pred[test_example] = self.classes_[np.argmax(counts)]
        return y_pred

    def score(self, X, y):
        """Calculate the score of the prediction.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)
            Data to score on.
        y : ndarray, shape (n_samples,)
            target values.

        Returns
        ----------
        score : float
            Accuracy of the model computed for the (X, y) pairs.
        """
        X = check_array(X)
        check_classification_targets(y)
        X, y = check_X_y(X, y)
        y_pred = self.predict(X)
        return np.sum(y_pred == y) / y.shape[0]


class MonthlySplit(BaseCrossValidator):
    """CrossValidator based on monthly split.

    Split data based on the given `time_col` (or default to index). Each split
    corresponds to one month of data for the training and the next month of
    data for the test.

    Parameters
    ----------
    time_col : str, defaults to 'index'
        Column of the input DataFrame that will be used to split the data. This
        column should be of type datetime. If split is called with a DataFrame
        for which this column is not a datetime, it will raise a ValueError.
        To use the index as column just set `time_col` to `'index'`.
    """

    def __init__(self, time_col='index'):  # noqa: D107
        self.time_col = time_col

    def get_n_splits(self, X, y=None, groups=None):
        """Return the number of splitting iterations in the cross-validator.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data, where `n_samples` is the number of samples
            and `n_features` is the number of features.
        y : array-like of shape (n_samples,)
            Always ignored, exists for compatibility.
        groups : array-like of shape (n_samples,)
            Always ignored, exists for compatibility.

        Returns
        -------
        n_splits : int
            The number of splits.
        """
        time_data = X[self.time_col] if self.time_col != 'index' else X.index
        if not pd.api.types.is_datetime64_any_dtype(time_data):
            raise ValueError("Not a datetime column.")
        else:
            time_data = pd.DatetimeIndex(time_data)
        month_data = time_data.month
        # print("MONTH",month_data)
        year_data = time_data.year
        m_y_pairs = list(zip(list(month_data), list(year_data)))
        # print("PAIRS", m_y_pairs)
        unique_pairs = list(set(m_y_pairs))
        # print('UNIQUE_PAIRS',unique_pairs)
        split = []
        for month, year in unique_pairs:
            if (month + 1, year) in unique_pairs:
                split.append((month, year, month + 1, year))
            if month == 12:
                if (1, year + 1) in unique_pairs:
                    split.append((month, year, 1, year + 1))
        split.sort()
        self.splits_ = split
        return len(split)

    def split(self, X, y, groups=None):
        """Generate indices to split data into training and test set.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data, where `n_samples` is the number of samples
            and `n_features` is the number of features.
        y : array-like of shape (n_samples,)
            Always ignored, exists for compatibility.
        groups : array-like of shape (n_samples,)
            Always ignored, exists for compatibility.

        Yields
        ------
        idx_train : ndarray
            The training set indices for that split.
        idx_test : ndarray
            The testing set indices for that split.
        """
        n_splits = self.get_n_splits(X, y, groups)
        old_order = list(X.index)

        # the following is necessary to handle non ordered time data
        if self.time_col != 'index':
            X = X.sort_values(by=self.time_col)
        else:
            X = X.sort_index()
        new_order = list(X.index)
        map_new2old = {new_order[i]: old_order.index(new_order[i])
                       for i in range(len(old_order))}

        time_data = X.index if self.time_col == 'index' else X[self.time_col]

        time_data_dti = pd.DatetimeIndex(time_data)
        new_order = np.array(new_order)
        for i in range(n_splits):
            month_train, year_train, month_test, year_test = self.splits_[i]
            MONTH = time_data_dti.month
            YEAR = time_data_dti.year
            train_dates = (MONTH == month_train) & (YEAR == year_train)
            idx_train = [map_new2old[i] for i in new_order[train_dates]]

            test_dates = (MONTH == month_test) & (YEAR == year_test)
            idx_test = [map_new2old[i] for i in new_order[test_dates]]

            yield (idx_train, idx_test)
