import json
import os
import sys

import pytest
from hypothesis_auto import auto_pytest_magic

from isort import main
from isort._version import __version__
from isort.settings import DEFAULT_CONFIG, Config
from isort.wrap_modes import WrapModes

auto_pytest_magic(main.sort_imports)


def test_iter_source_code(tmpdir):
    tmp_file = tmpdir.join("file.py")
    tmp_file.write("import os, sys\n")
    assert tuple(main.iter_source_code((tmp_file,), DEFAULT_CONFIG, [])) == (tmp_file,)


def test_sort_imports(tmpdir):
    tmp_file = tmpdir.join("file.py")
    tmp_file.write("import os, sys\n")
    assert main.sort_imports(str(tmp_file), DEFAULT_CONFIG, check=True).incorrectly_sorted
    main.sort_imports(str(tmp_file), DEFAULT_CONFIG)
    assert not main.sort_imports(str(tmp_file), DEFAULT_CONFIG, check=True).incorrectly_sorted

    skip_config = Config(skip=[str(tmp_file)])
    assert main.sort_imports(
        str(tmp_file), config=skip_config, check=True, disregard_skip=False
    ).skipped
    assert main.sort_imports(str(tmp_file), config=skip_config, disregard_skip=False).skipped


def test_is_python_file():
    assert main.is_python_file("file.py")
    assert main.is_python_file("file.pyi")
    assert main.is_python_file("file.pyx")
    assert not main.is_python_file("file.pyc")
    assert not main.is_python_file("file.txt")
    assert not main.is_python_file("file.pex")


def test_parse_args():
    assert main.parse_args([]) == {}
    assert main.parse_args(["--multi-line", "1"]) == {"multi_line_output": WrapModes.VERTICAL}
    assert main.parse_args(["--multi-line", "GRID"]) == {"multi_line_output": WrapModes.GRID}


def test_ascii_art(capsys):
    main.main(["--version"])
    out, error = capsys.readouterr()
    assert (
        out
        == f"""
                 _                 _
                (_) ___  ___  _ __| |_
                | |/ _/ / _ \\/ '__  _/
                | |\\__ \\/\\_\\/| |  | |_
                |_|\\___/\\___/\\_/   \\_/

      isort your imports, so you don't have to.

                    VERSION {__version__}

"""
    )
    assert error == ""


@pytest.mark.skipif(sys.platform == "win32", reason="cannot create fifo file on Windows platform")
def test_is_python_file_fifo(tmpdir):
    fifo_file = os.path.join(tmpdir, "fifo_file")
    os.mkfifo(fifo_file)
    assert not main.is_python_file(fifo_file)


def test_main(capsys, tmpdir):
    base_args = ["--settings-path", str(tmpdir), "--virtual-env", str(tmpdir)]

    # If no files are passed in the quick guide is returned
    main.main(base_args)
    out, error = capsys.readouterr()
    assert main.QUICK_GUIDE in out
    assert not error

    # Unless the config is requested, in which case it will be returned alone as JSON
    main.main(base_args + ["--show-config"])
    out, error = capsys.readouterr()
    returned_config = json.loads(out)
    assert returned_config
    assert returned_config["virtual_env"] == str(tmpdir)

    # This should work even if settings path is non-existent or not provided
    main.main(base_args[2:] + ["--show-config"])
    out, error = capsys.readouterr()
    assert json.loads(out)["virtual_env"] == str(tmpdir)
    main.main(
        base_args[2:]
        + ["--show-config"]
        + ["--settings-path", "/random-root-folder-that-cant-exist-right?"]
    )
    out, error = capsys.readouterr()
    assert json.loads(out)["virtual_env"] == str(tmpdir)


def test_isort_command():
    """Ensure ISortCommand got registered, otherwise setuptools error must have occured"""
    assert main.ISortCommand
