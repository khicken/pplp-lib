import private_set_intersection.python as psi

_FPR = 0.001
_DATA_STRUCTURE = psi.DataStructure.GCS


def psi_cardinality(set_a: set[str], set_b: set[str]) -> int:
    if not set_a or not set_b:
        return 0

    list_a = list(set_a)
    list_b = list(set_b)

    client = psi.client.CreateWithNewKey(reveal_intersection=False)
    server = psi.server.CreateWithNewKey(reveal_intersection=False)

    setup = server.CreateSetupMessage(_FPR, len(list_a), list_b, _DATA_STRUCTURE)
    request = client.CreateRequest(list_a)
    response = server.ProcessRequest(request)

    return client.GetIntersectionSize(setup, response)
