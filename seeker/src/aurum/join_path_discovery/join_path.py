# from join_column import JoinColumn
import random


class JoinPath:
    def __init__(self, join_key_list):
        self.join_path = join_key_list

    def to_str(self):
        format_str = ""
        for i, join_key in enumerate(self.join_path):
            format_str += join_key.tbl[:-4] + "." + join_key.col
            if i < len(self.join_path) - 1:
                format_str += " JOIN "
        return format_str

    def set_df(self, data_dic):
        for i, join_key in enumerate(self.join_path):
            join_key.dataset = data_dic[join_key.tbl]

    def print_metadata_str(self):
        print(self.to_str())
        for join_key in self.join_path:
            print(join_key.tbl[:-4] + "." + join_key.col)
            print(
                "datasource: {}, unique_values: {}, non_empty_values: {}, total_values: {}, join_card: {}, jaccard_similarity: {}, jaccard_containment: {}".format(
                    join_key.tbl,
                    join_key.unique_values,
                    join_key.total_values,
                    join_key.non_empty,
                    get_join_type(join_key.join_card),
                    join_key.js,
                    join_key.jc,
                )
            )

    def get_distance(self, join_path2):
        # return distance between the join paths

        return 0


class JoinKey:
    def __init__(self, col_drs, unique_values, total_values, non_empty):
        self.dataset = ""
        self.tbl = col_drs.source_name
        self.col = col_drs.field_name
        self.unique_values = unique_values
        self.total_values = total_values
        self.non_empty = non_empty
        if not hasattr(col_drs, 'metadata') or col_drs.metadata == 0:
            self.join_card = 0
            self.js = 0
            self.jc = 0
        else:
            self.join_card = col_drs.metadata["join_card"]
            self.js = col_drs.metadata["js"]
            self.jc = col_drs.metadata["jc"]


def get_join_type(join_card):
    if join_card == 0:
        return "One-to-One"
    elif join_card == 1:
        return "One-to-Many"
    elif join_card == 2:
        return "Many-to-One"
    else:
        return "Many-to-Many"


def find_farthest(distance_dic):
    max_dist = -1
    max_dis_index = -1
    for index in distance_dic.keys():
        if distance_dic[index] > max_dist:
            max_dist = distance_dic[index]
            max_dist_index = index

    print(max_dist, max_dist_index)
    return max_dist_index


def cluster_join_paths(joinable_lst, k):
    i = 0
    random.seed(0)
    centers = []
    assignment = {}
    distance = {}
    while i < k:
        if i == 0:
            centers.append(random.randint(0, len(joinable_lst)))
        else:
            centers.append(find_farthest(distance))
        # Assignment
        iter = 0
        for j in joinable_lst:
            if i == 0:
                assignment[j] = 0
                distance[iter] = j.get_distance(joinable_lst[centers[-1]])
            else:
                new_dist = j.get_distance(joinable_lst[centers[-1]])
                if (
                    new_dist < distance[iter]
                ):  # j.get_distance(joinable_lst[centers[assignment[j]]]):
                    assignment[j] = len(centers) - 1
                    distance[iter] = (
                        new_dist  # j.get_distance(joinable_lst[centers[-1]])
                    )
            iter += 1
            # update assignment

        i += 1
    return (centers, assignment)
