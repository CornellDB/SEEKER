import copy
import math
import random
from src.backend.group_querying import group_helper
from src.backend.qualityscore import profile_weights


def run_metam(tau,oracle,candidates,theta,metric,initial_df,new_col_lst,weights,class_attr,clusters,assignment,uninfo,epsilon):

# candidatees: centers 为中心的jc的index
# theta：希望达到的最小效用
# metrics： 目前的效用 U(Din)
# initial_df 原始的主表
# new col lst 候选的joincolumns
# profile 权重向量
# clusters： k是index 是这个cluster中的jc的列表
# assignment： key： jc v: 中心的index
# epsilon： 聚类半径


# 给每个聚类准备 Beta(1,1) 的计数器 likelihood_num/den。
# 论文 IV‑B “IDENTIFY‑GROUP – Thompson sampling” 把每个 cluster 看成一支 Bernoulli bandit；这里就是记录「成功次数 / 总次数」。
    likelihood_num=[]
    likelihood_den=[]
    for c in clusters:
        likelihood_num.append(1)
        likelihood_den.append(1)

    cluster_size={} # 统计每个cluster有多少个jc，是字典k：cluster 中心jc的index v:这个cluster有多少jc
    for k in assignment.keys():
        if assignment[k] in cluster_size.keys():
            cluster_size[assignment[k]]+=1
        else:
            cluster_size[assignment[k]]=1

#    for k in cluster_size.keys():
 #       print (k,centers[k],cluster_size[k])
        #print ("center details",new_col_lst[centers[k]].corr)
    stopping_criterion=1000#10000
    base_df=copy.deepcopy(initial_df)
    orig_metric = oracle.train_classifier(base_df,class_attr)
    fout=open("output.txt","w")
    total_queries=0
    iter=0 #最外圈大循环轮数counter
    grp_size=1  #组查询一次抽几列
    grp_queried_cand={}
    run_seq=True
    overall_queried={} #记录所有“被试过的列”和它带来的分数增益


# --------------------------------- 进入外层循环 --------------------

    while True: #代表 METAM 算法做一次“真正的增广”（augmentation）决策，也就是把 本轮 顺序查询或组查询里发现的最优列（或列组） 批量 地加入到主表 initial_df 中。外圈每跑完一次，就会比较本轮顺序查询(curr_max)和本轮组查询(curr_max_grp)哪个带来的增益更大，把对应的 max_candidate（或 max_candidate_grp）赋给 initial_df，并把 metric 更新为那个最大的效用值，然后 iter += 1 进入下一轮
        if metric >=theta: # metrics 目前最佳
            break

        i=0

        max_file=''         # # 记录本轮最优列对应的表和字段
        curr_max = metric   #  T* - 先设成旧的最好分数，之后更新成 本轮 单列查询 得到的最高分
        max_candidate=initial_df # 开始为原df，之后在seq query后加有用col
        max_jc ='' #本轮顺序查询中最优候选（JoinColumn）的索引
        if tau>1: #tau 内圈至少多少轮
            queried_cand = {}
        if tau==1 and iter==0:
            queried_cand={} # Q - 本轮测过的单条候选集合，k：中心index v：


        curr_max_grp = metric  # Tc* - 先设成旧的最好分数，之后更新成 本轮 组查询 得到的最高分


        max_grp_file=''
        max_candidate_grp=base_df

        while i<tau or curr_max <= metric:
            #Choose the candidate with maximum score
            if iter==0 or i==0:
                sorted_cand = profile_weights.sort_candidates(new_col_lst, candidates, weights, overall_queried) # 按照 candidate（中心）profile 加权算分，作为簇的分。然后排名中心。如果这个中心测过，则用测的增益作为打分。返回一个list，又分高到低排，list里面为tuple （中心index，分）
            print (sorted_cand)
            j=0
            # 找到第一个“本轮未试过”的候选 j
            while j<len(sorted_cand):
                if sorted_cand[j][0] in queried_cand.keys(): # 如果在Q里面就跳过，去看下一个在不在
                    j+=1
                    continue
                else:
                    break
                j+=1
            
            if j==len(sorted_cand):   # 若所有候选都已试过，则退出内层循环
                break

            #Query the candidate 
            print ("Chosen candidate in iteration ", i,len(queried_cand))
            print ("Candidate id and score ", sorted_cand[j])

            # --------- 一些优化 -------------

            if j>0 and sorted_cand[j][1]==0: # 如果不是第一名，且得分又 0→表示后面更差，直接结束序列查询
                candidate_id = sorted_cand[j][0]
                #fout.write("zero score"+new_col_lst[candidate_id].join_path.join_path[1].tbl+";"+new_col_lst[candidate_id].join_path.join_path[1].col+";"+new_col_lst[candidate_id].column+'\n')
                break#continue
            elif sorted_cand[j][1]==0:
                run_seq=False
            else:
                run_seq=True
            # 若总查询数超上限，也退出
            if total_queries > stopping_criterion:
                break

            # ---------- 开始测 -----------

            if run_seq:
                merged_df=copy.deepcopy(initial_df)
                candidate_id = sorted_cand[j][0]
                merged_df[new_col_lst[candidate_id].column]=new_col_lst[candidate_id].merged_df[new_col_lst[candidate_id].column]# 把jc中的要并入col 并入mergeddf，但是不能直接mergeddf=newcollst[id].mergeddf因为，mergeddf是累加的，包括之前并入的
                tmp_metric=max(oracle.train_classifier(merged_df,class_attr),metric) #用这个并入的mergeddf训练的结果，和目前最好间取最大
                print("iteration",tmp_metric,new_col_lst[candidate_id].join_path.join_path[1].tbl+";"+new_col_lst[candidate_id].join_path.join_path[1].col)
                #fout.write(new_col_lst[candidate_id].join_path.join_path[1].tbl+";"+new_col_lst[candidate_id].join_path.join_path[1].col+";"+new_col_lst[candidate_id].column+'\n')

                # 记录这次测试的增益到 Q，累加查询计数
                queried_cand[candidate_id] = tmp_metric-metric
                total_queries+=1
                fout.write(str(max(curr_max,curr_max_grp))+" "+str(total_queries)+"\n")
                if tmp_metric > curr_max: #如果有提升
                    curr_max=tmp_metric
                    max_candidate = merged_df  # 保存新的最佳表
                    max_file=new_col_lst[candidate_id].join_path.join_path[1].tbl+";"+new_col_lst[candidate_id].join_path.join_path[1].col
                    print ("metric",tmp_metric,new_col_lst[candidate_id].join_path.join_path[1].tbl)#,corr)
                    print(new_col_lst[candidate_id].profile_values)
                    print (merged_df)
                    max_jc = candidate_id

                #4a
                #break

#-----------------------------------上面为sequential 下面为group------------------------

            
            if len(list(grp_queried_cand.keys())) == len(new_col_lst): # 如果已经尝试过的组签名数量，等于所有候选列的数量，也就算这个grp-size能的都试了，那么扩大grpsize
                grp_size*=2

            # 从簇中去抽group的，返回jc_lst 要并入表的column对象，用字符串表示组合签名
            # (jc_lst,jc_representation)=group_helper.identify_group_query(new_col_lst,clusters,grp_size,likelihood_num,likelihood_den,grp_queried_cand) #纯likelihood版本
            (jc_lst, jc_representation) = group_helper.identify_group_query_thompson(new_col_lst, clusters, grp_size, likelihood_num, likelihood_den, grp_queried_cand) # thompson sampling 版本
            grp_merged_df=copy.deepcopy(base_df)
            for jc in jc_lst:
                grp_merged_df[jc.column]=jc.merged_df[jc.column] # 然后把 jc_lst 里的每条增广列都贴上去，形成一张新的“组增广后”表
            #fout.write(jc_lst[0].join_path.join_path[1].tbl+";"+jc_lst[0].join_path.join_path[1].col+";"+jc_lst[0].column+'\n')
            tmp_metric=max(oracle.train_classifier(grp_merged_df,class_attr),orig_metric)


            #询只抽到 1 条列（len(jc_lst)==1）并且它确实带来增益（tmp_metric>orig_metric），就把该列的索引 loc 重新加入 candidates，以便下次顺序查询时能再次重点尝试。同时把它的“真实增益”记录到本轮 queried_cand，方便排序函数后用。
            if tmp_metric > orig_metric and len(jc_lst)==1:
                candidates.append(jc_lst[0].loc)
            if len(jc_lst)==1: #
                queried_cand[jc_lst[0].loc] = tmp_metric-orig_metric
                #if tmp_metric-orig_metric > 0:
                #    candidates.append(jc_lst[0].loc)

            # 任何组查询结果都记入 grp_queried_cand，
            # key 用 jc_representation 保证同一组不重复试
            grp_queried_cand[jc_representation] = tmp_metric
            total_queries+=1
            fout.write(str(max(curr_max,curr_max_grp))+" "+str(total_queries)+"\n")


            # 如果这组的 tmp_metric 比本轮之前最佳组 curr_max_grp 更高，
            # 就更新 curr_max_grp 和对应的增广后表 max_candidate_grp
            if tmp_metric > curr_max_grp:
                curr_max_grp=tmp_metric
                max_candidate_grp = grp_merged_df
                print ("metric",tmp_metric,new_col_lst[candidate_id].join_path.join_path[1].tbl)#,corr)
                max_grp_file=new_col_lst[candidate_id].join_path.join_path[1].tbl+";"+new_col_lst[candidate_id].join_path.join_path[1].col
                print(new_col_lst[candidate_id].profile_values)
                print (grp_merged_df)


            #Likelihood update
            # “后验更新”——用这次组查询的结果来调整
            # 该组中每条列所属簇的成功/尝试计数
            # 如果 tmp_metric > orig_metric，则视为一次“成功”
            for jc in jc_lst:
                clust_id=assignment[jc]
                if tmp_metric>orig_metric:
                    likelihood_num[clust_id]+=1
                likelihood_den[clust_id]+=1

            if iter==0:
                weights= profile_weights.get_weights(new_col_lst, queried_cand, weights)
                #if len(list(queried_cand.keys())) > 10:
                #    print (weights)
            i+=1

        # 若整体查询次数 total_queries 已超过设定上限，就立即退出外层循环，停止算法。
        weights= profile_weights.get_weights(new_col_lst, queried_cand, weights)
        if total_queries>stopping_criterion:
            break






        '''
            论文中提到，如果一个簇内增广路径的“真实增益”差异很大（即 profile 不能很好地预测），就不能仅靠抽样簇后验来覆盖，可能漏掉高收益的列。
        
            做法：
        
            对每个簇随机抽 ⌈log₂(|簇|)⌉ 条路径测试增益，统计它们的分数列表 queried_lst。
        
            若超过一半的测试分数偏离平均分 mean_sc 超过比例 ε，就认定该簇“不均质”。
        
            对“不均质簇”，一次性把簇内所有列的索引都加回 candidates，确保后续序列查询会逐条覆盖它们。
        '''




        if iter==0 and tau>1: #外层循环的第 0 轮（iter==0）且参数 tau>1 时才执行后续均质性检测。这样保证只检查一次，不在每轮都反复做
            cl_iter=0
            k=len(clusters)
            while cl_iter < k:
                lst=clusters[cl_iter]  # 第一个cluster 的jc列表
                #Get a sample of lst to check if homogenous
                samp_iter=0
                irregularity_count=0

                count=math.ceil(math.log(len(lst))/math.log(2))   # cluster 中有多少 jc， 得到log（jc）/log（2）
                print (len(lst),count)
                if count <=1: #若 count ≤ 1（簇内元素太少），跳过本簇的检测，进入下一个簇。
                    cl_iter+=1
                    continue

                #Utility of center
                queried_lst=[]

                while samp_iter<count:
                    curr_samp=lst[random.randint(0,len(lst)-1)]
                    merged_df=copy.deepcopy(initial_df)
                    merged_df[curr_samp.column]=curr_samp.merged_df[curr_samp.column]#从cluster中随机抽一个列，并并入 mergeddf

                    if not curr_samp in queried_cand.keys(): #若本抽样列此前未在 queried_cand（本轮顺序查询记录）出现，则视为一次新查询，total_queries 自增。
                        total_queries+=1

                    tmp_metric=max(oracle.train_classifier(merged_df,class_attr),metric) # 看这个随机加入的带来的提升
                    queried_cand[curr_samp] = tmp_metric-metric
                    queried_lst.append(tmp_metric)

#如果这次抽样的效用超过了本轮顺序查询的最佳 curr_max，就更新：curr_max 为 tmp_metric | max_candidate 为此时的 merged_df | max_file 记录对应表名和列名 | max_jc 标记这条最佳 JoinColumn 的索引
                    if tmp_metric > curr_max:
                        curr_max=tmp_metric
                        max_candidate = merged_df
                        max_file=curr_samp.join_path.join_path[1].tbl+";"+curr_samp.join_path.join_path[1].col
                        print ("metric",tmp_metric,curr_samp.join_path.join_path[1].tbl)#,corr)
                        print (merged_df)
                        max_jc = curr_samp.loc
                    #    irregularity_count+=1
                    fout.write(str(max(curr_max,curr_max_grp))+" "+str(total_queries)+"\n")
                    samp_iter+=1
                
                #Check mean (1+epsilon)
                print (queried_lst)
                mean_sc=sum(queried_lst)* 1.0/len(queried_lst) #打印所有抽样效用值 queried_lst，计算它们的平均值 mean_sc。

                count=0 #遍历每个抽样值 v，若其与平均 mean_sc 的偏差超过比例 ε（高于 mean_sc*(1+ε) 或低于 mean_sc/(1+ε)），则 count 自增
                for v in queried_lst:
                    if v > mean_sc*(1+epsilon) or v < mean_sc*1.0/(1+epsilon):
                        count+=1


                if count > len(queried_lst)/2: #若“偏离次数” count 超过一半，说明当前簇“不均质”。此时打印提示，并**把该簇内所有成员的索引 c.loc**全量追加回 candidates，确保之后序列查询会逐条尝试。
                    print ("not a homogenous cluster", mean_sc, count, len(lst))
                    for c in lst:
                        candidates.append(c.loc)
                
                # fout1=open('log.txt','a')
                # fout1.write(str(cl_iter)+" cluster count "+str(count)+" "+str(len(queried_lst))+"\n")
                # fout1.close()
                cl_iter+=1
            #Check clusters and update candidates
        print ("length of candidates",len(candidates))
        print ("Chosen first augmentation", curr_max,metric)
        print (max_jc)
        #print ("Max table and column are ", new_col_lst[max_jc].join_path.join_path[1].tbl,new_col_lst[max_jc].join_path.join_path[1].col)







        #外圈本轮结束后：选最终增广 & 迭代器更新
        '''
        若组查询最佳 curr_max_grp 优于顺序查询 curr_max，就把 max_candidate_grp 作为新的 initial_df，并更新 metric。
        
        如果都没提升（curr_max == metric），iter += 1 然后 continue 返回外圈顶端，再做下一轮（不加任何列）。
        
        否则顺序查询更好，就用 max_candidate 和 curr_max。
        '''


        for c in queried_cand.keys():
            overall_queried[c]=queried_cand[c] #把本轮 queried_cand 内容合并到 overall_queried
        if curr_max_grp > curr_max: #若组查询最佳 curr_max_grp 优于顺序查询 curr_max，就把 max_candidate_grp 作为新的 initial_df，并更新 metric
            metric = curr_max_grp
            initial_df = max_candidate_grp
            fout1=open('log.txt','a')
            fout1.write("OuterLoop group query wins. "+ "File, Col: " +max_grp_file+ " Metric " + str(metric)+"\n")
            fout1.close()
        elif curr_max==metric:#如果都没提升,再做下一轮（不加任何列）
            iter+=1
            continue
        else:               #否则顺序查询更好，就用 max_candidate 和 curr_max。
            metric = curr_max
            fout1=open('log.txt','a')
            fout1.write("OuterLoop seque query wins: "+ "File, Col: "+max_file+ " Metric: " +str(metric)+"\n")
            fout1.close()
            initial_df = max_candidate


       
        iter+=1


    return (initial_df)
