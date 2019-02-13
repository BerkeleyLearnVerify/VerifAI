# This files defiens the error table as a panda object
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from dotmap import DotMap


class error_table():
    def __init__(self, space):
        self.space= space
        self.column_names = []
        self.column_type = {}
        for i in range(space.fixedFlattenedDimension):
            self.column_names.append(space.meaningOfFlatCoordinate(i))
            self.column_type[space.meaningOfFlatCoordinate(i)] = \
                space.coordinateIsNumerical(i)
        self.table = pd.DataFrame(columns=self.column_names)
        self.ignore_locs = []


    def update_column_names(self, column_names):
        assert len(self.table.columns) == len(column_names)
        self.table.columns = column_names
        self.column_names = column_names

    def update_error_table(self, sample):
        sample = self.space.flatten(sample, fixedDimension=True)
        sample_dict = {}
        for k, v in zip(self.table.columns, list(sample)):
            if np.any(np.array(sample) == None):
                locs = np.where(np.array(sample) == None)
                self.ignore_locs = self.ignore_locs + list(locs[0])
            sample_dict[k] = float(v) if self.column_type[k] and v is not None else v
        self.ignore_locs = list(set(tuple(self.ignore_locs)))
        self.table = self.table.append(sample_dict, ignore_index=True)


    def get_column_by_index(self, index):
        if isinstance(index, int):
            index = list([index])
        if len(index) < 1:
            print("No indices provided: returning all samples")
        elif max(index) >= len(self.table.columns):
            for i in index:
                if i >= len(self.table.columns):
                    index.remove(i)
            print("Tried to access index not in error table")
        if len(self.table) > 0:
            names_index = self.table.columns[index]
            return self.table[names_index]
        else:
            print("No entries in error table yet")
        return None

    def get_column_by_name(self, column_names):
        index = []
        if isinstance(column_names, str):
            if column_names in self.table.columns:
                index.append(column_names)
        else:
            for s in column_names:
                if s in self.table.columns:
                    index.append(s)
        return self.table[index]

    def get_samples_by_index(self, index):
        if isinstance(index, int):
            index = list([index])
        if max(index) >= len(self.table):
            print("Trying to access samples not in the table")
            for i in index:
                if i >= len(self.table):
                    index.remove(i)
        return self.table.iloc[index]

    def split_table(self, column_names=None):
        if column_names is None:
            column_names = self.column_names
        numerical, categorical = [], []
        for c in column_names:
            if self.column_type[c]:
                numerical.append(c)
            else:
                categorical.append(c)
        return self.get_column_by_name(numerical), self.get_column_by_name(categorical)

    def get_random_samples(self, count=5):
        if count > len(self.table):
            return list(range(len(self.table)))
        else:
            sample_ids = set()
            while len(sample_ids) < count:
                i = np.random.randint(len(self.table))
                sample_ids.add(i)
            return list(sample_ids)

    def k_closest_samples(self, column_names=None, k = None):
        # Returns the indices of the samples that are the closest to each other
        if len(self.table) < 1:
            return []

        num_samples = len(self.table)

        if column_names is None:
            column_names = self.column_names

        numerical, categorical = self.split_table(column_names=column_names)

        if len(categorical.columns) + len(numerical.columns) == 0:
            return []


        if k is None or k >= num_samples:
             return np.array(range(num_samples))

        # Standardize tables (only for numerical table)
        stats = numerical.describe()
        standardized_dict = {r:(numerical[r] - stats[r]['mean'])/stats[r]['std']
                             for r in numerical.columns}
        standardized_table = pd.DataFrame(standardized_dict)

        # Norm distance between table rows
        if len(numerical.columns) > 0:
            d_rows = [np.linalg.norm(standardized_table.values -
                                 standardized_table.values[i], axis=1)
                  for i in range(len(standardized_table))]
        else:
            d_rows = [0] * num_samples

        # For the categorical rows we want define distance as the number of different rows

        normalize_row = len(categorical.columns) + len(numerical.columns)
        if len(categorical.columns) > 0:
            d_cat_rows = [np.apply_along_axis(sum , 1,
                        categorical.values != categorical.iloc[i].values)/normalize_row
                      for i in range(len(categorical))]
            d_rows = np.array(d_rows) + np.array(d_cat_rows)


        # Now the row associated with the min sum is the largest set of correlated elements
        sum_rows = []
        correlated_rows = []
        for r in d_rows:
            ks = np.argpartition(r, k)[:k]
            sum_rows.append(sum(r[ks]))
            correlated_rows.append(ks)

        return correlated_rows[np.array(sum_rows).argmin()]

    def pca_analysis(self, column_names=None, n_components= 1):
        # Returns the direction of the principal component among the samples
        if len(self.table) < 1:
            return

        if column_names is None:
            column_names = self.column_names

        numerical, _ = self.split_table(column_names=column_names)


        # Do PCA analysis only on the numerical columns
        if len(numerical.columns) == 0:
            return
        pca_columns = []
        for c in numerical.columns:
            if c in self.table.columns and c not in self.table.columns[self.ignore_locs]:
                pca_columns.append(c)

        table = self.get_column_by_name(pca_columns)

        # PCA components
        if n_components > min(len(table), len(table.columns)):
            n_components = min(len(table), len(table.columns))

        pca = PCA(n_components=n_components)
        pca.fit(table)

        return {'columns':pca_columns, 'pivot': table.mean().values, 'directions': pca.components_}

    def analyze(self, analysis_params=None):
        analysis_data = DotMap()
        if analysis_params is None or ('pca' in analysis_params and analysis_params.pca) or 'pca' not in analysis_params:
            if analysis_params is not None and 'pca_params' in analysis_params:
                columns = analysis_params.pca_params.columns \
                    if 'columns' in analysis_params.pca_params else None
                n_components = analysis_params.pca_params.n_components \
                    if 'n_components' in analysis_params.pca_params else 1
            else:
                columns, n_components = None, 1
            analysis_data.pca = self.pca_analysis(column_names=columns, n_components=n_components)

        if analysis_params is None or ('k_closest' in analysis_params and analysis_params.k_closest) or 'k_closest' not in analysis_params:
            if analysis_params is not None and 'k_closest_params' in analysis_params:
                columns = analysis_params.k_closest_params.columns \
                    if 'columns' in analysis_params.k_closest_params else None
                k = analysis_params.k_closest_params.k \
                    if 'k' in analysis_params.k_closest_params else None
            else:
                columns, k = None, None
            analysis_data.k_closest = self.k_closest_samples(column_names=columns, k=k)


        if analysis_params is None or ('random' in analysis_params and analysis_params.random) or 'random' not in analysis_params:
            if analysis_params is not None and 'random_params' in analysis_params:
                count = analysis_params.random_params.count \
                    if 'count' in analysis_params.random_params else 5
            else:
                count = 5
            analysis_data.random = self.get_random_samples(count=count)

        return analysis_data





