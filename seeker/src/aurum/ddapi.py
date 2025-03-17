from api.apiutils import Operation
from api.apiutils import OP
from api.apiutils import Relation
from api.apiutils import DRS
from api.apiutils import DRSMode
from api.apiutils import Hit
from api.apiutils import compute_field_id as id_from


class DDAPI:

    __network = None

    def __init__(self, network):
        self.__network = network

    """
    Seed API
    """

    def drs_from_raw_field(self, field: (str, str, str)) -> DRS:
        """
        Given a field and source name, it returns a DRS with its representation
        :param field: a tuple with the name of the field, (db_name, source_name, field_name)
        :return: a DRS with the source-field internal representation
        """
        db, source, field = field
        nid = id_from(db, source, field)
        h = Hit(nid, db, source, field, 0)
        return self.drs_from_hit(h)

    def drs_from_hit(self, hit: Hit) -> DRS:
        drs = DRS([hit], Operation(OP.ORIGIN))
        return drs

    def drs_from_hits(self, hits: [Hit]) -> DRS:
        drs = DRS(hits, Operation(OP.ORIGIN))
        return drs

    def drs_from_table(self, source: str) -> DRS:
        """
        Given a source, it retrieves all fields of the source and returns them
        in the internal representation
        :param source: string with the name of the table
        :return: a DRS with the source-field internal representation
        """
        hits = self.__network.get_hits_from_table(source)
        drs = DRS([x for x in hits], Operation(OP.ORIGIN))
        return drs

    def drs_from_table_hit(self, hit: Hit) -> DRS:
        table = hit.source_name
        hits = self.__network.get_hits_from_table(table)
        drs = DRS([x for x in hits], Operation(OP.TABLE, params=[hit]))
        return drs

    def drs_expand_to_table(self, drs: DRS) -> DRS:
        o_drs = DRS([], Operation(OP.NONE))
        for h in drs:
            table = h.source_name
            hits = self.__network.get_hits_from_table(table)
            drs = DRS([x for x in hits], Operation(OP.TABLE, params=[h]))
            o_drs.absorb(drs)
        return o_drs

    def reverse_lookup(self, nid) -> [str]:
        info = self.__network.get_info_for([nid])
        return info


class API(DDAPI):

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)


if __name__ == "__main__":
    print("Aurum API")
