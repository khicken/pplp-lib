from pplp.psi import psi_cardinality


def test_basic_intersection():
    a = {"alice", "bob", "charlie"}
    b = {"bob", "charlie", "dave"}
    assert psi_cardinality(a, b) == 2


def test_no_intersection():
    a = {"alice", "bob"}
    b = {"charlie", "dave"}
    assert psi_cardinality(a, b) == 0


def test_empty_set_a():
    assert psi_cardinality(set(), {"a", "b"}) == 0


def test_empty_set_b():
    assert psi_cardinality({"a", "b"}, set()) == 0


def test_both_empty():
    assert psi_cardinality(set(), set()) == 0


def test_identical_sets():
    s = {"a", "b", "c"}
    assert psi_cardinality(s, s) == 3


def test_single_element_match():
    assert psi_cardinality({"x"}, {"x"}) == 1


def test_single_element_no_match():
    assert psi_cardinality({"x"}, {"y"}) == 0
