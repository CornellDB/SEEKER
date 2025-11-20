import copy
import pandas as pd
from src.backend.profiles.base_profile import BaseProfile
from metam.config import Config
from src.backend.profiles.corr_profile import CorrProfile
from src.backend.profiles.mutual_profile import MutualInfoProfile
from src.backend.profiles.syntactics_profile import SyntacticProfile
from src.backend.profiles.chi2_profile import Chi2Profile
from src.backend.profiles.semantic_profile import SemanticProfile
from src.backend.profiles.coverage_profile import CoverageProfile
from src.backend.profiles.uninform_profile import UninformativeProfile

class JoinColumn:
    def __init__(self, join_path,df,column,base_df,class_attr,array_loc,uninformative=0, profilers: list[BaseProfile] | None = None, local_config=None):
        #print ("initiating")
        self.join_path = join_path
        self.loc=array_loc
        #self.dataset=dataset
        self.column=column # column 就是你从「右表」（外表）里选出来，然后通过 key_r（连接键）join 到主表上、当作新特征的一整列。
        self.orig_name=column
        self.base_copy=copy.deepcopy(base_df)
        self.df = df.drop_duplicates(
            subset=self.join_path.join_path[1].col,
            keep="first"
        ).copy()
        self.class_attr=class_attr

        self.key_r=self.join_path.join_path[1].col #key_r（连接键）, join_path[0] 左表joinkey join_path[1] 右表joinkey
        
# 避免新引入的列名（不管是你要 join 进来的那一列，还是用来 join 的键）和主表里已有的列重名

        # 如果候选列名冲突，就直接重命名
        if self.column in base_df.columns:
            new_name = f"{self.column}_new"
            self.df = self.df.rename(columns={self.column: new_name})
            self.column = new_name

        # 如果连接键也冲突，再重命名一次
        if self.key_r in base_df.columns:
            new_name = f"{self.key_r}_new"
            self.df = self.df.rename(columns={self.key_r: new_name})
            self.key_r = new_name

        '''
        collst=list(base_df.columns)
        collst.append(self.column)
        self.merged_df=pd.merge(self.base_copy,self.df[[self.key_r,self.column]],left_on=self.join_path.join_path[0].col,right_on=self.key_r,how="left")
        self.merged_df=self.merged_df[collst]
        '''
# 主表与外表合并,只保留原主表列 + 新特征列。若合并失败（缺少键列等），则回退：复制主表并新增一列全 0。
        try:
            #print (self.join_path.join_path[1].col,self.join_path.join_path[0].col)
            #print (self.column)
            collst=list(base_df.columns)
            collst.append(self.column)
            # 左连接：主表所有行保留，外表按 key_r 对齐
            self.merged_df=pd.merge(self.base_copy,self.df[[self.key_r,self.column]],left_on=self.join_path.join_path[0].col,right_on=self.key_r,how="left")
            # 只保留原主表列 + 新特征列
            self.merged_df=self.merged_df[collst]

        except:
            self.merged_df=copy.deepcopy(self.base_copy)
            self.merged_df[self.column]=0
            #Add 0 as the profile


        
        #self.merged_df[self.column]=self.merged_df[self.column].fillna(0)
        #print ("merged",self.merged_df)
#把所有字符串（object）列转换成类别编码（整数）

        self.copied_df=copy.deepcopy(self.merged_df)

        for c in self.copied_df.columns:
            if self.copied_df.dtypes[c]=='object':
                self.copied_df[c]=self.copied_df[c].astype('category')
                self.copied_df[c]=self.copied_df[c].cat.codes
        #print (self.copied_df.dtypes)

# 初始化存放 profile 的字典
        if profilers is None:
            profilers = local_config.profiler_factory(self.orig_name, uninformative)


        # compute and store all profile scores
        self.profile_values: dict[str, dict[str, float]] = {}
        for profiler in profilers:
            self.profile_values[profiler.name()] = profiler.score(
                self.copied_df, self.column
            )



    def get_distance(self, other: "JoinColumn") -> float:
        """
        Compute a simple max-difference distance between this column and another,
        across all profile dimensions.
        """
        max_dist = 0.0
        for prof_name, scores in self.profile_values.items():
            other_scores = other.profile_values.get(prof_name, {})
            for col_name, my_val in scores.items():
                other_val = other_scores.get(col_name, 0.0)
                diff = abs(my_val - other_val)
                if diff > max_dist:
                    max_dist = diff
        return max_dist
