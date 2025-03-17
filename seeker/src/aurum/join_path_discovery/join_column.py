import math, copy
import pandas as pd


class JoinColumn:
    def __init__(self, join_path, dataset, column, base_df):
        self.join_path = join_path
        self.dataset = dataset
        self.column = column
        base_copy = copy.deepcopy(base_df)
        df = self.dataset.df.drop_duplicates(
            subset=self.join_path.join_path[1].col, keep="first"
        )
        try:
            merged_df = pd.merge(
                base_copy,
                df[[self.join_path.join_path[1].col, column]],
                left_on=self.join_path.join_path[0].col,
                right_on=self.join_path.join_path[1].col,
                how="left",
            )
            self.corr = merged_df[self.column].corr(merged_df["n. collisions"])
            # self.corr=dataset.df[column].corr(base_df['class'])
            if math.isnan(self.corr):
                self.corr = 0
        except:
            self.corr = 0

    def get_distance(self, jc2):
        return abs((self.corr) - jc2.corr)

        # Option 1: correlation between columns
        try:
            corr = self.dataset.df[self.column].corr(jc2.dataset.df[jc2.column])
        except:
            corr = 0
        return 1 - abs(corr)
