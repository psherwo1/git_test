"""components.timber_roof -- RETIRED (v5_harbour_house round 2, reuse mandate).

Round 1's verge_boards (a bargeboard with crossed gable horns) duplicated linear_roof's verge finish.  It is folded
into components.linear_roof as an option, WITHOUT the horns (note 16: the village's finial vocabulary instead):

    linear_roof(g, roof, covering="shingle", verge="board", apex_finial="turned")

No building imports this module.  It is kept only as this pointer (the file can be deleted at the producer's merge).
"""


def verge_boards(*_a, **_k):
    raise NotImplementedError("timber_roof.verge_boards is retired: use linear_roof(..., verge='board', "
                              "apex_finial='turned') (kit 1.12)")


__all__ = ["verge_boards"]
