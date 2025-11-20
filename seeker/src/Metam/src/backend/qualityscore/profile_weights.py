import operator
from sklearn import datasets, linear_model

def initialize_weights(jc,weights):
    proflst= jc.profile_values.keys() # 这个jc的profile指标 eg sim
    for prof in proflst:
        collst=jc.profile_values[prof].keys() # profile中的指标比如sim中date
        for col in collst:
            weights [(prof,col)]=1 # 那就(sim， date)权重为1
    return weights


def sort_candidates_irrespective (new_col_lst,candidates,weights,queried_cand):
    score_dic = {}
    for c in candidates:
        jc=new_col_lst[c]
        #print (c,jc.profile_values)
        sc = 0
        for w in weights.keys():
            sc+= abs(float(jc.profile_values[w[0]][w[1]]) * weights[w])
        score_dic[c] = sc
    sorted_sc = sorted(score_dic.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_sc

def sort_candidates (new_col_lst,candidates,weights,queried_cand):
    score_dic = {}
    for c in candidates:
        if c in queried_cand.keys():
            score_dic[c]=queried_cand[c]
            #print ("queried score is ",score_dic[c])
            continue
        jc=new_col_lst[c]
        #print (c,jc.profile_values)
        sc = 0
        for w in weights.keys():
            sc+= abs(float(jc.profile_values[w[0]][w[1]]) * weights[w])
        score_dic[c] = sc
    sorted_sc = sorted(score_dic.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_sc


def get_features(profile_dic: dict[str, dict[str, float]],
                 prof_lst: list[str]) -> list[float]:# 把profile展平，比如以前是嵌套dict nan:all:0.75, corr:A:1, B:2，现在变成0.75， 1， 1
    """
    把 profile_dic 中每个 profile 的所有键按自然排序拉出来拼成一维向量。

    profile_dic 例子：
      {
        "corr": {"A":0.2, "B":0.5, ...},
        "mutual": {"A":0.01, "B":0.03, ...},
        "coverage": {"all":0.75},
        "semantic": {"all":0.12},
        "uninfo": {"0":0.33, "1":0.54, ...}
      }
    prof_lst 顺序决定拼接时各 profile 的先后顺序。
    """
    features = []
    for prof in prof_lst:
        subdic = profile_dic[prof]
        # 对键做自然排序：数字优先按数值，小写字母按字母序
        keys = sorted(
            subdic.keys(),
            key=lambda k: int(k) if k.isdigit() else k
        )
        for k in keys:
            features.append(subdic[k])
    return features

def get_weights(new_col_lst, queried_cand, weights):
    X, Y = [], []
    prof_lst = list(new_col_lst[0].profile_values.keys())

    for idx, gain in queried_cand.items():
        feats = get_features(new_col_lst[idx].profile_values, prof_lst)
        X.append(feats)
        Y.append(gain)

    if not X:
        return weights

    regr = linear_model.LinearRegression().fit(X, Y)
    coefs = regr.coef_

    # 按同样顺序写回 weights
    ptr = 0
    for prof in prof_lst:
        subdic = new_col_lst[0].profile_values[prof]
        keys = sorted(subdic.keys(), key=lambda k: int(k) if k.isdigit() else k)
        for k in keys:
            weights[(prof, k)] = coefs[ptr]
            ptr += 1

    return weights

