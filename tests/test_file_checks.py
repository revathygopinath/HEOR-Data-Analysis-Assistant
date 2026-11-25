import pytest

from validation.file_checks import FileCheckError, load_csv


def test_good_csv_loads():
    df = load_csv("demo.csv", b"age,sex\n50,Male\n60,Female\n")
    assert df.shape == (2, 2)          # 2 rows, 2 columns


def test_wrong_extension_is_rejected():
    with pytest.raises(FileCheckError):
        load_csv("demo.xlsx", b"age\n50\n")


def test_empty_file_is_rejected():
    with pytest.raises(FileCheckError):
        load_csv("demo.csv", b"")


def test_headers_but_no_rows_is_rejected():
    with pytest.raises(FileCheckError):
        load_csv("demo.csv", b"age,sex\n")


def test_repeated_column_names_are_rejected():
    with pytest.raises(FileCheckError):
        load_csv("demo.csv", b"age,age\n50,60\n")