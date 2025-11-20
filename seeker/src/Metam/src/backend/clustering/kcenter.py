import random
import math
def find_farthest(distance_dic):
    max_dist=-1
    max_dis_index=-1
    for index in distance_dic.keys():
        if distance_dic[index]>max_dist:
            max_dist=distance_dic[index]
            max_dist_index=index

    print (max_dist,max_dist_index)
    return max_dist_index


def get_clusters(assignment,k):
    clusters=[]
    i=0
    while i<k:
        clusters.append([])
        i+=1

    for c in assignment.keys():
        lst=clusters[assignment[c]]
        lst.append(c)
        clusters[assignment[c]]=lst
    return clusters

def cluster_join_paths(joinable_lst,k,epsilon):
    i=0 # 当前已经选出的中心数（初始为0）。
    random.seed(0)
    centers=[] #存放被选为“中心”的索引列表,也就是拿其中的一些joincolumn对象作为中心
    assignment={} # 记录每个对象分配到哪个中心
    distance={} # 记录每个对象到其“当前所属中心”的距离
    max_dist=0 # 当前批次中所有对象到其最近中心时的最大距离。
    while i<k:
        if i==0:
            centers.append(random.randint(0,len(joinable_lst)-1)) #第一个中心随机选
        else:
            centers.append(find_farthest(distance)) #后续中心选“离已有中心最远”的那个
        #Assignment
        iter=0
        for j in joinable_lst:
            if i==0:
                assignment[j]=0 #第一次（只有一个中心）时：分到中心
                distance[iter]=j.get_distance(joinable_lst[centers[-1]]) #记录 j 到这个唯一中心的距离 = 0
                if distance[iter]>max_dist:
                    max_dist=distance[iter]
            else:
                new_dist=j.get_distance(joinable_lst[centers[-1]])
                if new_dist < distance[iter]:#j.get_distance(joinable_lst[centers[assignment[j]]]):
                    assignment[j]=len(centers)-1
                    distance[iter]=new_dist#j.get_distance(joinable_lst[centers[-1]])
                    if distance[iter]>max_dist:
                        max_dist=distance[iter]
            iter+=1
                    #update assignment
        if max_dist<epsilon:
            break
        i+=1
    return (centers,assignment,get_clusters(assignment,k))
