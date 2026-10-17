"""components.timber_finish -- RETIRED (v5_harbour_house round 2, reuse mandate).

Round 1's thin wrappers on the composite cull and decals are folded into components.composite as options:

    composite_hidden_cull(g, parts=composite.BACKED_PARTS)        the backed-parts-only cull
    composite_decals(g, timber=True, waterfront=True, ...)        + composite.timber_anchors / waterfront_anchors

No building imports this module.  It is kept only as this pointer (the file can be deleted at the producer's merge).
"""


def timber_hidden_cull(*_a, **_k):
    raise NotImplementedError("timber_finish is retired: use composite.composite_hidden_cull(parts=BACKED_PARTS)")


def timber_decals(*_a, **_k):
    raise NotImplementedError("timber_finish is retired: use composite.composite_decals(timber=True, waterfront=True)")


__all__ = ["timber_hidden_cull", "timber_decals"]
