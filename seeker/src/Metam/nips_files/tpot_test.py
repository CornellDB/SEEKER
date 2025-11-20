import tpot
import numpy as np
import pandas as pd
import itertools
from sklearn.pipeline import make_pipeline

# Create D_in (input df), D_test(test df for eval), and D_repo (list of dfs)
df = pd.read_csv("Iris.csv").sample(frac=1, random_state=42).reset_index(drop=True)
rows_per_split = int(np.ceil(len(df) / 5))
iris_dfs = [df.iloc[i:i + rows_per_split, :] for i in range(0, len(df), rows_per_split)]
iris_in = iris_dfs[0]
iris_repo = iris_dfs[1:4]
iris_test = iris_dfs[4]


def call_metam(df_in, df_repo, df_test, task):
    """
    Call to the Metam API.
    input:
     df_in: input df
     df_repo: repository of dfs
     df_test: testing df
     task: task type
    """
    return df_in


def get_acc(predicted, true):
    num_equal = 0
    for i in range(len(true)):
        if predicted[i] == true[i]:
            num_equal += 1
        # else:
        #     print(f"Wrong prediction: {i}th row")
    return num_equal / len(true)


def get_all_augmentations(df_in, df_repo):
    """
    input:
     df_in: input df to be augmented
     df_repo: repository of dfs used to augment df_in
    output:
     a list of augmented dfs
    """
    # Get all subsets from df_repo, appended with df_in
    augmented_dfs = []
    for i in range(1, len(df_repo) + 1):
        for subset in itertools.combinations(df_repo, i):
            cur_subset = list(subset)
            cur_subset.append(df_in)
            augmented_df = pd.concat(cur_subset, ignore_index=True)
            # print(len(augmented_df))
            augmented_dfs.append(augmented_df)
    return augmented_dfs


def get_automl_model_acc(df_in, df_test):
    """
    input:
     df_in: input df used for training
     df_test: testing df used to eval acc
    output:
     a (model, acc) pair
    """
    tpot_model = tpot.TPOTClassifier(generations=1,
                                     population_size=10,
                                     verbosity=0,
                                     random_state=42,
                                     max_eval_time_mins=1)
    X_train = df_in.iloc[:, :-1].values
    y_train = df_in.iloc[:, -1].values
    X_test = df_test.iloc[:, :-1].values
    y_test = df_test.iloc[:, -1].values
    tpot_model.fit(X_train, y_train)
    predicted = tpot_model.predict(X_test)
    acc = get_acc(predicted, y_test)
    return tpot_model, acc


def base_one(df_in, df_test):
    """
    Baseline 1: autoML only
    """
    return get_automl_model_acc(df_in, df_test)


def base_two(df_in, df_repo, df_test):
    """
    Baseline 2: Enumerate all possible augmentations. Run autoML over all augmentations.
    """
    augmented_dfs = get_all_augmentations(df_in, df_repo)
    # best_df = None
    best_model = None
    best_acc = 0
    for cur_df in augmented_dfs:
        cur_model, cur_acc = get_automl_model_acc(cur_df, df_test)
        # print("acc for current model is", cur_acc)
        if cur_acc > best_acc:
            # best_df = cur_df
            best_model = cur_model
            best_acc = cur_acc
    return best_model, best_acc


def base_three(df_in, df_repo, df_test):
    """
    Baseline 3: Run Metam with automl
    """
    df_aug = call_metam(df_in, df_repo, df_test, "automl")
    return get_automl_model_acc(df_aug, df_test)


def base_four(df_in, df_repo, df_test):
    """
    Baseline 4: Use rf as input task to Metam. Use autoML on the output data.
    """
    df_aug = call_metam(df_in, df_repo, df_test, "random_forest")
    return get_automl_model_acc(df_aug, df_test)


def base_five(df_in, df_repo, df_test, num_iters):
    """
    Baseline 5: Run Metam to get data -> choose a model for this data ->
                based on this model output from previous step, try to find data again
    """
    cur_df = df_in
    cur_model = "automl"
    for i in range(num_iters):
        cur_df = call_metam(cur_df, df_repo, df_test, cur_model)
        tpot_model = tpot.TPOTClassifier(generations=1,
                                         population_size=10,
                                         verbosity=0,
                                         random_state=42,
                                         max_eval_time_mins=1)
        X_train = cur_df.iloc[:, :-1].values
        y_train = cur_df.iloc[:, -1].values
        tpot_model.fit(X_train, y_train)
        best_pipeline = tpot_model.fitted_pipeline_
        best_classifier = best_pipeline.steps[-1][1]
        new_model = make_pipeline(best_classifier)
        new_model.fit(X_train, y_train)
        cur_model = new_model
    X_test = df_test.iloc[:, :-1].values
    y_test = df_test.iloc[:, -1].values
    predicted = cur_model.predict(X_test)
    acc = get_acc(predicted, y_test)
    return cur_model, acc


model_1, acc_1 = base_one(iris_in, iris_test)
print(f"Accuracy of baseline one is {acc_1}")

model_2, acc_2 = base_two(iris_in, iris_repo, iris_test)
print(f"Accuracy of baseline two is {acc_2}")

model_3, acc_3 = base_three(iris_in, iris_repo, iris_test)
print(f"Accuracy of baseline three is {acc_3}")

model_4, acc_4 = base_four(iris_in, iris_repo, iris_test)
print(f"Accuracy of baseline four is {acc_4}")

model_5, acc_5 = base_five(iris_in, iris_repo, iris_test, 2)
print(f"Accuracy of baseline five is {acc_5}")
