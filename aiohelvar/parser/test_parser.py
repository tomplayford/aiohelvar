
from aiohelvar.parser.address import HelvarAddress

def test_helvar_address_equality():

    a = HelvarAddress(1,2,3,4)
    b = HelvarAddress(1,2,3,4)

    assert a==b, "Address should be equal"

def test_helvar_address_non_equality():

    a = HelvarAddress(1,3,3,4)
    b = HelvarAddress(1,2,3,4)

    assert a!=b, "Address should not be equal"

def test_helvar_address_equality_short():

    a = HelvarAddress(1,2)
    b = HelvarAddress(1,2)

    assert a==b, "Address should be equal"

def test_helvar_address_non_equality_short():

    a = HelvarAddress(1,3)
    b = HelvarAddress(1,2)

    assert a!=b, "Address should not be equal"