import pandas as pd
from src.backend.core.join_column import JoinColumn
import random
def get_column_lst(joinable_lst):
    i=0
    skip_count=0
    new_col_lst=[]
    while i<len(joinable_lst):
        print (i,len(new_col_lst))
        jp=joinable_lst[i]
        print (jp.join_path[0].tbl,jp.join_path[0].col,jp.join_path[1].tbl,jp.join_path[1].col)
        if jp.join_path[1].tbl in ignore_lst or jp.join_path[0].tbl in ignore_lst:
            i+=1
            continue
        if jp.join_path[1].tbl=='s27g-2w3u.csv'or jp.join_path[0].tbl=='s27g-2w3u.csv':
            skip_count+=1
            i+=1
            continue
        if jp.join_path[0].tbl in size_dic.keys() and jp.join_path[1].tbl in size_dic.keys():
            if size_dic[jp.join_path[0].tbl]>1000000 or size_dic[jp.join_path[1].tbl]>1000000:
                skip_count+=1
                i+=1
                continue


        if jp.join_path[0].tbl not in data_dic.keys():
            df_l=pd.read_csv(path+"/"+jp.join_path[0].tbl,low_memory=False)
            data_dic[jp.join_path[0].tbl]=df_l
            print ("dataset size is ",df_l.shape)
        else:
            df_l=data_dic[jp.join_path[0].tbl]
        if jp.join_path[1].tbl not in data_dic.keys():
            df_r=pd.read_csv(path+"/"+jp.join_path[1].tbl,low_memory=False)
            data_dic[jp.join_path[1].tbl]=df_r
            print ("dataset size is ",df_r.shape)
        else:
            df_r=data_dic[jp.join_path[1].tbl]
        collst=list(df_r.columns)
        if jp.join_path[1].col not in df_r.columns or jp.join_path[0].col not in df_l.columns:
            i+=1
            continue
        if df_r.dtypes[jp.join_path[1].col] == 'float64' or df_r.dtypes[jp.join_path[1].col] == 'int64':
            skip_count+=1
            i+=1
            continue
        for col in collst:
            if jp.join_path[1].tbl=='2013_NYC_School_Survey.csv' or jp.join_path[1].tbl =='5a8g-vpdd.csv':
                continue
            if col==jp.join_path[1].col or jp.join_path[0].col =='class' or col=='class':
                continue
            jc=JoinColumn(jp,df_r,col,base_df,class_attr,len(new_col_lst),uninfo)
            new_col_lst.append(jc)
            if jc.column=='School Type' and jp.join_path[1].tbl=='bnea-fu3k.csv':#2012-2013 ENVIRONMENT GRADE':# and jp.join_path[1].tbl=='test1.csv':
                f1=open('log.txt','a')
                f1.write(str(len(new_col_lst)-1)+" "+jc.column+" "+jc.join_path.join_path[1].tbl+" "+jc.join_path.join_path[1].col+"\n")
                print(col,jc.merged_df,len(new_col_lst)-1,"test1")
                f1.close()
        i+=1
    return (new_col_lst,skip_count)

class JoinPath:
    def __init__(self, join_key_list):
        self.join_path = join_key_list #长度为 2 的列表，包括两个joinkey，一个表示“左表 join 键 +一个表示 右表 join 键

    def to_str(self):
        format_str = ""
        for i, join_key in enumerate(self.join_path):
            format_str += join_key.tbl[:-4] + '.' + join_key.col
            if i < len(self.join_path) - 1:
                format_str += " JOIN "
        return format_str

    def set_df(self,data_dic):
        for i, join_key in enumerate(self.join_path):
            join_key.dataset=data_dic[join_key.tbl]# 给join_path中左，右表 绑定它对应的 DataFrame。

    def print_metadata_str(self):
        print(self.to_str())
        for join_key in self.join_path:
            print(join_key.tbl[:-4] + "." + join_key.col)
            print("datasource: {}, unique_values: {}, non_empty_values: {}, total_values: {}, join_card: {}, jaccard_similarity: {}, jaccard_containment: {}"
            .format(join_key.tbl, join_key.unique_values, join_key.total_values, join_key.non_empty, get_join_type(join_key.join_card), join_key.js, join_key.jc))

    def get_distance(self,join_path2):
        #return distance between the join paths

        return 0

class JoinKey: #表示一个表和其一列
    def __init__(self, col_drs, unique_values, total_values, non_empty):
        self.dataset=''
        try:
            self.tbl = col_drs.source_name # 存一个表
            self.col = col_drs.field_name # 一个列
        except:
            self.tbl=''
            self.col=''

        self.unique_values = unique_values
        self.total_values = total_values
        self.non_empty = non_empty
        try: 
           if col_drs.metadata == 0:
                self.join_card = 0
                self.js = 0
                self.jc = 0
           else:
                self.join_card = col_drs.metadata['join_card']
                self.js = col_drs.metadata['js']
                self.jc = col_drs.metadata['jc']
        except:
            self.js=0
def get_join_type(join_card):
    if join_card == 0:
        return "One-to-One"
    elif join_card == 1:
        return "One-to-Many"
    elif join_card == 2:
        return "Many-to-One"
    else:
        return "Many-to-Many"


def get_join_paths_from_file(querydata,filepath):
    df=pd.read_csv(filepath)

    # joinpath df中要有4列
    # querydata就是主表名字，比如train。csv

    subdf=df[df['tbl1']==querydata] #主表名字在左边，也就是主表在左
    subdf2=df[df['tbl2']==querydata] # 主表名字在右边，也就是主表在右

    options=[] #集所有生成的 JoinPath 对象。

    for index,row in subdf.iterrows(): #对于path中主表在左的那些行
        jk1=JoinKey('','',0,0)
        jk2=JoinKey('','',0,0)

        # 左表table 和column
        jk1.tbl=row['tbl1']
        jk1.col=row['col1']
        #右表table 和column
        jk2.tbl=row['tbl2']
        jk2.col=row['col2']

        # 左边 joinkey包括table， col； 右边joinkey包括 右表table col
        # 俩合并在一起 表示一个join path
        ret_jp = JoinPath([jk1,jk2])

        options.append(ret_jp)


    for index,row in subdf2.iterrows():#对于path中主表在右的那些行
        jk1=JoinKey('','',0,0)
        jk2=JoinKey('','',0,0)
        jk1.tbl=row['tbl1']
        jk1.col=row['col1']

        jk2.tbl=row['tbl2']
        jk2.col=row['col2']
        ret_jp = JoinPath([jk2,jk1])
        options.append(ret_jp)
    print(options)

    return options
