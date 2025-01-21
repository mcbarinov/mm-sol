from mm_solana.account import (
    check_private_key,
    generate_account,
    get_keypair,
    get_private_key_arr_str,
    get_private_key_base58,
    get_public_key,
    is_valid_pubkey,
)


def test_check_private_key():
    public_key = "2b8bUknUbyLmUdKPH6o4jUbgNeztKSVwCN5w2QtEm61r"
    private_key = "[100,43,148,189,179,174,228,31,193,2,233,109,26,249,247,176,51,187,172,105,83,69,170,251,45,160,23,57,212,255,9,236,23,154,5,130,7,89,91,131,59,109,150,73,105,110,198,19,222,132,173,40,62,99,162,166,44,212,129,180,49,177,253,181]"  # noqa: E501
    assert check_private_key(public_key, private_key)

    public_key = "2b8bUknUbyLmUdKPH6o4jUbgNeztKSVwCN5w2QtEm61r"
    private_key = [
        100,
        43,
        148,
        189,
        179,
        174,
        228,
        31,
        193,
        2,
        233,
        109,
        26,
        249,
        247,
        176,
        51,
        187,
        172,
        105,
        83,
        69,
        170,
        251,
        45,
        160,
        23,
        57,
        212,
        255,
        9,
        236,
        23,
        154,
        5,
        130,
        7,
        89,
        91,
        131,
        59,
        109,
        150,
        73,
        105,
        110,
        198,
        19,
        222,
        132,
        173,
        40,
        62,
        99,
        162,
        166,
        44,
        212,
        129,
        180,
        49,
        177,
        253,
        181,
    ]
    assert check_private_key(public_key, private_key)

    public_key = "5pPavVyApDBxVQfssMGDY25dGdUfC27pTn4PygRPzFmn"
    private_key = "2nNCy96F9b11mnbrhmKn1ETdFEc6uEfaVaM5e9crn1qJmVMZnt6bMqBYhVDZt5BrhaYToJyZznK1twgF77sm63Re"
    assert check_private_key(public_key, private_key)


def test_generate_account():
    acc_1 = generate_account()
    acc_2 = generate_account()

    assert acc_1.public_key != acc_2.public_key
    assert len(acc_1.private_key_arr) == 64


def test_get_keypair():
    acc = get_keypair("2nNCy96F9b11mnbrhmKn1ETdFEc6uEfaVaM5e9crn1qJmVMZnt6bMqBYhVDZt5BrhaYToJyZznK1twgF77sm63Re")
    assert str(acc.pubkey()) == "5pPavVyApDBxVQfssMGDY25dGdUfC27pTn4PygRPzFmn"

    acc = get_keypair(
        "[82,64,164,208,0,155,36,201,208,109,43,74,205,156,170,228,146,161,5,178,220,84,195,1,26,161,196,249,242,208,176,186,132,228,144,215,19,161,75,120,161,187,133,19,177,120,198,161,218,5,75,159,126,193,98,18,233,227,129,128,197,153,227,104]",
    )
    assert str(acc.pubkey()) == "9wkxjGXrRhHB9pFZrEpQKBKAJ52jMjVUahnVNezJFvL7"


def test_get_public_key():
    private_key = "2eP4yM63zQxBkoF2Rzzmank9AQ2qiPJExxb7AZ95UPxUpHf8XWgYpy7C5ZNy6zU3jj4nYPD1ijK4EzLLZDwkxZXM"
    assert get_public_key(private_key) == "9wkxjGXrRhHB9pFZrEpQKBKAJ52jMjVUahnVNezJFvL7"


def test_get_private_key_base58():
    private_key = "[82,64,164,208,0,155,36,201,208,109,43,74,205,156,170,228,146,161,5,178,220,84,195,1,26,161,196,249,242,208,176,186,132,228,144,215,19,161,75,120,161,187,133,19,177,120,198,161,218,5,75,159,126,193,98,18,233,227,129,128,197,153,227,104]"  # noqa: E501
    res = "2eP4yM63zQxBkoF2Rzzmank9AQ2qiPJExxb7AZ95UPxUpHf8XWgYpy7C5ZNy6zU3jj4nYPD1ijK4EzLLZDwkxZXM"
    assert get_private_key_base58(private_key) == res


def test_get_private_key_arr_str():
    private_key = "2eP4yM63zQxBkoF2Rzzmank9AQ2qiPJExxb7AZ95UPxUpHf8XWgYpy7C5ZNy6zU3jj4nYPD1ijK4EzLLZDwkxZXM"
    res = "[82,64,164,208,0,155,36,201,208,109,43,74,205,156,170,228,146,161,5,178,220,84,195,1,26,161,196,249,242,208,176,186,132,228,144,215,19,161,75,120,161,187,133,19,177,120,198,161,218,5,75,159,126,193,98,18,233,227,129,128,197,153,227,104]"  # noqa: E501
    assert get_private_key_arr_str(private_key) == res


def test_is_valid_pubkey():
    assert is_valid_pubkey("9nmjQrSpmf51BxcQu6spWD8w4jUzPVrtmtPbDGLyDuan")
    assert is_valid_pubkey("9nmjQrSpmf51BxcQu6spWD8w4jUzPVrtmtPbDGLyDuaN")
    assert not is_valid_pubkey("9nmjQrSpmf51BxcQu6spWD8w4jUzPVrtmtPbDGLyDuama")
